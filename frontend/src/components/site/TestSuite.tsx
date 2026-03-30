import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { GitBranch, MoreVertical, Plus, Calendar, List, Database, Play } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  useTestSuitesQuery,
  useCreateTestSuiteMutation,
  useUpdateTestSuiteMutation,
  useDeleteTestSuiteMutation,
  useRunTestSuiteMutation,
} from '@/utils/queries/testSuiteQueries'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import { ConfirmModal } from '../common/ConfirmModal'
import TestSuiteBuilder from './TestSuiteBuilder'
import type { TestSuite as TestSuiteType, FlowDefinition, TestSuiteStatus } from '@/types/testSuite'

// ─── Status Badge ─────────────────────────────────────────────────────────────

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-500 border-gray-200',
  ready: 'bg-green-50 text-green-600 border-green-200',
  running: 'bg-blue-50 text-blue-600 border-blue-200',
  done: 'bg-emerald-50 text-emerald-600 border-emerald-200',
  failed: 'bg-red-50 text-[#fc0101] border-red-200',
}

const SuiteStatusBadge: React.FC<{ status: string }> = ({ status }) => (
  <span
    className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded border tracking-wide ${
      statusColors[status] || statusColors.draft
    }`}
  >
    {status}
  </span>
)

// ─── Suite Card ───────────────────────────────────────────────────────────────

interface SuiteCardProps {
  suite: TestSuiteType
  onEdit: (suite: TestSuiteType) => void
  onDelete: (suite: TestSuiteType) => void
  onRun: (suite: TestSuiteType) => void
}

const SuiteCard: React.FC<SuiteCardProps> = ({ suite, onEdit, onDelete, onRun }) => {
  const nodeCount = suite.flow_definition?.nodes?.filter(
    n => n.type === 'step' || n.type === 'suite-ref',
  ).length ?? 0
  const edgeCount = suite.flow_definition?.edges?.length ?? 0

  return (
    <div className="border border-[#E4D7D7] bg-white rounded-[6px] hover:shadow-sm transition-shadow">
      <div className="bg-[#FFF8F8] border-b border-[#E4D7D7] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-[#fc0101]" />
          <h3 className="text-sm font-semibold text-[#333]">{suite.title}</h3>
        </div>
        <div className="flex items-center gap-2">
          <SuiteStatusBadge status={suite.status} />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="p-1.5 hover:bg-[#f6f3f3] rounded cursor-pointer">
                <MoreVertical className="w-4 h-4 text-gray-500" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => onRun(suite)}
                className="cursor-pointer text-sm flex items-center gap-2 text-emerald-600"
              >
                <Play className="w-3.5 h-3.5" />
                Run Test Suite
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onEdit(suite)} className="cursor-pointer text-sm">
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onDelete(suite)}
                className="cursor-pointer text-sm text-red-500"
              >
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <div className="p-4">
        {suite.description && (
          <p className="text-xs text-gray-500 mb-3 line-clamp-2">{suite.description}</p>
        )}
        <div className="flex gap-4">
          <StatItem icon={<List className="w-3.5 h-3.5" />} label="Nodes" value={nodeCount} />
          <StatItem icon={<GitBranch className="w-3.5 h-3.5" />} label="Edges" value={edgeCount} />
          <StatItem
            icon={<Database className="w-3.5 h-3.5" />}
            label="Test Cases"
            value={suite.test_case_count ?? 0}
          />
          {suite.created_on && (
            <StatItem
              icon={<Calendar className="w-3.5 h-3.5" />}
              label="Created"
              value={new Date(suite.created_on).toLocaleDateString()}
              isText
            />
          )}
        </div>
      </div>
    </div>
  )
}

const StatItem: React.FC<{
  icon: React.ReactNode
  label: string
  value: number | string
  isText?: boolean
}> = ({ icon, label, value, isText }) => (
  <div className="flex items-center gap-1.5 text-xs text-gray-500">
    <span className="text-gray-400">{icon}</span>
    <span className="text-[10px]">{label}:</span>
    <span className={`font-semibold ${isText ? 'text-gray-500' : 'text-[#333]'}`}>{value}</span>
  </div>
)

// ─── Main Component ───────────────────────────────────────────────────────────

const TestSuite: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const siteId = Number(id)
  const queryClient = useQueryClient()

  const { data, isLoading } = useTestSuitesQuery(siteId)
  const { mutate: createSuite, isPending: isCreating } = useCreateTestSuiteMutation()
  const { mutate: updateSuite, isPending: isUpdating } = useUpdateTestSuiteMutation()
  const { mutate: deleteSuite, isPending: isDeleting } = useDeleteTestSuiteMutation()
  const { mutate: runSuite, isPending: isRunning } = useRunTestSuiteMutation()

  const [builderOpen, setBuilderOpen] = useState(false)
  const [editingSuite, setEditingSuite] = useState<TestSuiteType | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<TestSuiteType | null>(null)
  const [runTarget, setRunTarget] = useState<TestSuiteType | null>(null)

  const suites = data?.items || []

  const handleOpenCreate = () => {
    setEditingSuite(null)
    setBuilderOpen(true)
  }

  const handleOpenEdit = (suite: TestSuiteType) => {
    setEditingSuite(suite)
    setBuilderOpen(true)
  }

  const handleBuilderSave = (payload: {
    title: string
    description: string
    status: string
    flow_definition: FlowDefinition
    scenario_count: number
    test_case_count: number
  }) => {
    const typedPayload = { ...payload, status: payload.status as TestSuiteStatus }
    if (editingSuite) {
      updateSuite(
        { suiteId: editingSuite.id, payload: typedPayload },
        {
          onSuccess: () => {
            toast.success('Test suite updated')
            setBuilderOpen(false)
            setEditingSuite(null)
          },
          onError: () => toast.error('Failed to update test suite'),
        },
      )
    } else {
      createSuite(
        { site_id: siteId, ...typedPayload },
        {
          onSuccess: () => {
            toast.success('Test suite created')
            setBuilderOpen(false)
          },
          onError: () => toast.error('Failed to create test suite'),
        },
      )
    }
  }

  const handleRun = (suite: TestSuiteType) => {
    setRunTarget(suite)
  }

  const handleConfirmDelete = () => {
    if (!deleteTarget) return
    deleteSuite(
      { suiteId: deleteTarget.id, siteId },
      {
        onSuccess: () => {
          toast.success('Test suite deleted')
          setDeleteTarget(null)
        },
        onError: () => {
          toast.error('Failed to delete test suite')
          setDeleteTarget(null)
        },
      },
    )
  }

  return (
    <div className="flex flex-col gap-5">
      {/* ── Header ── */}
      <div className="border border-[#E4D7D7] bg-white rounded-[6px]">
        <div className="bg-[#FFF8F8] border-b border-[#E4D7D7] px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-[#fc0101]" />
            <h2 className="text-[15px] font-semibold">Test Suites</h2>
            {data && (
              <span className="text-xs text-gray-400 bg-[#f6f3f3] border border-[#E4D7D7] rounded-full px-2 py-0.5">
                {data.total}
              </span>
            )}
          </div>
          <button
            onClick={handleOpenCreate}
            className="flex items-center gap-1.5 text-sm text-[#fc0101] border border-[#fc0101] px-3 py-1.5 rounded hover:bg-red-50 cursor-pointer transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Suite
          </button>
        </div>

        {/* ── Suite Grid ── */}
        <div className="p-4">
          {isLoading ? (
            <div className="text-sm text-gray-400 py-6 text-center">Loading…</div>
          ) : suites.length === 0 ? (
            <div className="flex flex-col items-center py-10 gap-3 text-center">
              <GitBranch className="w-10 h-10 text-[#E4D7D7]" />
              <p className="text-sm text-gray-400">No test suites yet.</p>
              <button
                onClick={handleOpenCreate}
                className="text-sm text-[#fc0101] border border-[#fc0101] px-4 py-1.5 rounded hover:bg-red-50 cursor-pointer"
              >
                Create your first test suite
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              {suites.map(suite => (
                <SuiteCard
                  key={suite.id}
                  suite={suite}
                  onEdit={handleOpenEdit}
                  onDelete={s => setDeleteTarget(s)}
                  onRun={handleRun}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Builder Dialog ── */}
      {builderOpen && (
        <TestSuiteBuilder
          siteId={siteId}
          editSuite={editingSuite}
          onClose={() => { setBuilderOpen(false); setEditingSuite(null) }}
          onSaved={() => queryClient.invalidateQueries({ queryKey: ['test-suites', siteId] })}
          onSave={handleBuilderSave}
          isSaving={isCreating || isUpdating}
        />
      )}

      {/* ── Delete Confirm ── */}
      <ConfirmModal
        open={!!deleteTarget}
        title="Delete Test Suite"
        message={`Are you sure you want to delete "${deleteTarget?.title}"? This cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />

      {/* ── Run Confirm ── */}
      <ConfirmModal
        open={!!runTarget}
        title="Run Test Suite"
        message={`Run "${runTarget?.title}"? This will execute all ${runTarget?.scenario_count ?? 0} scenarios and ${runTarget?.test_case_count ?? 0} test cases.`}
        confirmText="Run"
        cancelText="Cancel"
        variant="default"
        isLoading={isRunning}
        onConfirm={() => {
          if (!runTarget) return
          runSuite(runTarget.id, {
            onSuccess: (execution) => {
              toast.success(
                `Execution started for "${runTarget.title}" (ID: ${execution.id})`,
              )
              setRunTarget(null)
            },
            onError: () => {
              toast.error(`Failed to start execution for "${runTarget.title}"`)
              setRunTarget(null)
            },
          })
        }}
        onCancel={() => setRunTarget(null)}
      />
    </div>
  )
}

export default TestSuite
