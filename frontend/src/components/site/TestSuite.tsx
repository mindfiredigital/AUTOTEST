import React, { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { Plus, Search, ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  useTestSuitesQuery,
  useCreateTestSuiteMutation,
  useUpdateTestSuiteMutation,
  useDeleteTestSuiteMutation,
  useRunTestSuiteMutation,
} from '@/utils/queries/testSuiteQueries'
import { ConfirmModal } from '../common/ConfirmModal'
import { Pagination } from '../common/Pagination'
import { DynamicTable } from '../table/DynamicTable'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import TestSuiteBuilder from './TestSuiteBuilder'
import { ExecutionResultModal } from './TestSuite/ExecutionResultModal'
import { formatDateDDMMYYYY } from '@/utils/helper'
import type { TableColumn, TableAction } from '../table/types'
import type { TestSuite as TestSuiteType, FlowDefinition, TestSuiteStatus } from '@/types/testSuite'

// ─── Status badge ─────────────────────────────────────────────────────────────

const statusColors: Record<string, string> = {
  draft:            'bg-gray-100    text-gray-500   border-gray-200',
  ready:            'bg-green-50    text-green-600  border-green-200',
  running:          'bg-blue-50     text-blue-600   border-blue-200',
  done:             'bg-emerald-50  text-emerald-600 border-emerald-200',
  failed:           'bg-red-50      text-[#fc0101]  border-red-200',
  passed:           'bg-emerald-50  text-emerald-600 border-emerald-200',
  partially_passed: 'bg-amber-50    text-amber-600  border-amber-200',
  error:            'bg-orange-50   text-orange-600 border-orange-200',
}

const SuiteStatusBadge: React.FC<{ status: string }> = ({ status }) => (
  <span
    className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded border tracking-wide whitespace-nowrap ${
      statusColors[status] || statusColors.draft
    }`}
  >
    {status.replace('_', ' ')}
  </span>
)

// ─── Statuses that have an execution result ───────────────────────────────────

const HAS_RESULT_STATUSES = new Set(['done', 'failed', 'running', 'passed', 'partially_passed', 'error'])

const STATUS_OPTIONS = [
  { value: 'all',     label: 'All Statuses' },
  { value: 'draft',   label: 'Draft' },
  { value: 'ready',   label: 'Ready' },
  { value: 'running', label: 'Running' },
  { value: 'done',    label: 'Done' },
  { value: 'failed',  label: 'Failed' },
]

type SortKey = 'created_on' | 'title' | 'test_case_count' | 'status'
type SortDir = 'asc' | 'desc'

// ─── Sort icon helper ─────────────────────────────────────────────────────────

const SortIcon: React.FC<{ col: SortKey; sortKey: SortKey; sortDir: SortDir }> = ({ col, sortKey, sortDir }) => {
  if (sortKey !== col) return <ChevronsUpDown className="inline w-3 h-3 ml-1 text-gray-300" />
  return sortDir === 'asc'
    ? <ChevronUp className="inline w-3 h-3 ml-1 text-[#fc0101]" />
    : <ChevronDown className="inline w-3 h-3 ml-1 text-[#fc0101]" />
}

// ─── Main Component ───────────────────────────────────────────────────────────

const TestSuite: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const siteId = Number(id)
  const queryClient = useQueryClient()

  const [page, setPage]   = useState(1)
  const [limit, setLimit] = useState(10)

  const { data, isLoading } = useTestSuitesQuery(siteId, page, limit)
  const { mutate: createSuite, isPending: isCreating } = useCreateTestSuiteMutation()
  const { mutate: updateSuite, isPending: isUpdating } = useUpdateTestSuiteMutation()
  const { mutate: deleteSuite, isPending: isDeleting } = useDeleteTestSuiteMutation()
  const { mutate: runSuite,    isPending: isRunning   } = useRunTestSuiteMutation()

  const [builderOpen,   setBuilderOpen]   = useState(false)
  const [editingSuite,  setEditingSuite]  = useState<TestSuiteType | null>(null)
  const [deleteTarget,  setDeleteTarget]  = useState<TestSuiteType | null>(null)
  const [runTarget,     setRunTarget]     = useState<TestSuiteType | null>(null)
  const [resultSuite,   setResultSuite]   = useState<TestSuiteType | null>(null)

  // ── Search / filter / sort state ──────────────────────────────────────────
  const [search,      setSearch]      = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortKey,     setSortKey]     = useState<SortKey>('created_on')
  const [sortDir,     setSortDir]     = useState<SortDir>('desc')

  const rawSuites  = data?.items ?? []
  const totalItems = data?.total ?? 0

  // ── Client-side filter + sort ─────────────────────────────────────────────

  const displaySuites = useMemo(() => {
    let result = [...rawSuites]

    if (search.trim()) {
      const q = search.toLowerCase()
      result = result.filter(
        (s) =>
          s.title.toLowerCase().includes(q) ||
          (s.description ?? '').toLowerCase().includes(q),
      )
    }

    if (statusFilter !== 'all') {
      result = result.filter((s) => s.status === statusFilter)
    }

    result.sort((a, b) => {
      let aVal: string | number = ''
      let bVal: string | number = ''

      if (sortKey === 'created_on') {
        aVal = a.created_on ?? ''
        bVal = b.created_on ?? ''
      } else if (sortKey === 'title') {
        aVal = a.title.toLowerCase()
        bVal = b.title.toLowerCase()
      } else if (sortKey === 'test_case_count') {
        aVal = a.test_case_count ?? 0
        bVal = b.test_case_count ?? 0
      } else if (sortKey === 'status') {
        aVal = a.status
        bVal = b.status
      }

      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDir === 'asc' ? 1  : -1
      return 0
    })

    return result
  }, [rawSuites, search, statusFilter, sortKey, sortDir])

  const totalPages = Math.max(1, Math.ceil(totalItems / limit))

  // ── Sort toggle ────────────────────────────────────────────────────────────

  const toggleSort = (col: SortKey) => {
    if (sortKey === col) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(col)
      setSortDir('asc')
    }
  }

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleOpenCreate = () => { setEditingSuite(null); setBuilderOpen(true) }
  const handleOpenEdit   = (suite: TestSuiteType) => { setEditingSuite(suite); setBuilderOpen(true) }

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
          onSuccess: () => { toast.success('Test suite updated'); setBuilderOpen(false); setEditingSuite(null) },
          onError:   () => toast.error('Failed to update test suite'),
        },
      )
    } else {
      createSuite(
        { site_id: siteId, ...typedPayload },
        {
          onSuccess: () => { toast.success('Test suite created'); setBuilderOpen(false) },
          onError:   () => toast.error('Failed to create test suite'),
        },
      )
    }
  }

  const handleConfirmDelete = () => {
    if (!deleteTarget) return
    deleteSuite(
      { suiteId: deleteTarget.id, siteId },
      {
        onSuccess: () => { toast.success('Test suite deleted'); setDeleteTarget(null) },
        onError:   () => { toast.error('Failed to delete test suite'); setDeleteTarget(null) },
      },
    )
  }

  const handleConfirmRun = () => {
    if (!runTarget) return
    runSuite(runTarget.id, {
      onSuccess: (execution) => {
        toast.success(`Execution started for "${runTarget.title}" (ID: ${execution.id})`)
        setRunTarget(null)
      },
      onError: () => { toast.error(`Failed to start execution for "${runTarget.title}"`); setRunTarget(null) },
    })
  }

  // ── Table columns ──────────────────────────────────────────────────────────

  const columns: TableColumn<TestSuiteType>[] = [
    {
      key: 'created_on',
      header: (
        <button onClick={() => toggleSort('created_on')} className="flex items-center cursor-pointer select-none">
          Date <SortIcon col="created_on" sortKey={sortKey} sortDir={sortDir} />
        </button>
      ),
      width: 'w-[120px]',
      render: (s) => (
        <span className="text-xs text-gray-500">
          {s.created_on ? formatDateDDMMYYYY(s.created_on) : '—'}
        </span>
      ),
    },
    {
      key: 'title',
      header: (
        <button onClick={() => toggleSort('title')} className="flex items-center cursor-pointer select-none">
          Title <SortIcon col="title" sortKey={sortKey} sortDir={sortDir} />
        </button>
      ),
      width: 'w-[180px]',
      render: (s) => (
        <div className="text-sm font-semibold text-[#333] truncate">{s.title}</div>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      render: (s) => (
        <span className="text-xs text-gray-500 truncate block">
          {s.description || <span className="text-gray-300">—</span>}
        </span>
      ),
    },
    {
      key: 'scenario_count',
      header: 'Nodes',
      width: 'w-[80px]',
      align: 'center',
      render: (s) => (
        <span className="text-sm text-gray-600">
          {s.flow_definition?.nodes?.filter(n => n.type === 'step' || n.type === 'suite-ref').length ?? 0}
        </span>
      ),
    },
    {
      key: 'edges',
      header: 'Edges',
      width: 'w-[80px]',
      align: 'center',
      render: (s) => (
        <span className="text-sm text-gray-600">
          {s.flow_definition?.edges?.length ?? 0}
        </span>
      ),
    },
    {
      key: 'test_case_count',
      header: (
        <button onClick={() => toggleSort('test_case_count')} className="flex items-center cursor-pointer select-none">
          Test Cases <SortIcon col="test_case_count" sortKey={sortKey} sortDir={sortDir} />
        </button>
      ),
      width: 'w-[100px]',
      align: 'center',
      render: (s) => (
        <span className="text-sm text-gray-600">{s.test_case_count ?? 0}</span>
      ),
    },
    {
      key: 'status',
      header: (
        <button onClick={() => toggleSort('status')} className="flex items-center justify-center w-full cursor-pointer select-none">
          Status <SortIcon col="status" sortKey={sortKey} sortDir={sortDir} />
        </button>
      ),
      width: 'w-[150px]',
      align: 'center',
      render: (s) => <SuiteStatusBadge status={s.status} />,
    },
  ]

  // ── Table actions ──────────────────────────────────────────────────────────

  const actions: TableAction<TestSuiteType>[] = [
    {
      label: 'Run Test Suite',
      disabled: (s) => s.status === 'running',
      onClick:  (s) => setRunTarget(s),
    },
    {
      label:  'View Results',
      hidden: (s) => !HAS_RESULT_STATUSES.has(s.status),
      onClick: (s) => setResultSuite(s),
    },
    {
      label:   'Edit',
      onClick: (s) => handleOpenEdit(s),
    },
    {
      label:       'Delete',
      destructive: true,
      onClick:     (s) => setDeleteTarget(s),
    },
  ]

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-5">

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-4 pb-4">
        {/* Search */}
        <div className="relative w-72">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            placeholder="Search suites…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            className="pl-8"
          />
        </div>

        {/* Status filter */}
        <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1) }}>
          <SelectTrigger className="w-[160px] cursor-pointer">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* New Suite button */}
        <button
          onClick={handleOpenCreate}
          className="ml-auto flex items-center gap-1.5 text-sm text-[#fc0101] border border-[#fc0101] px-3 py-1.5 rounded hover:bg-red-50 cursor-pointer transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Suite
        </button>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-sm text-gray-400 py-10 text-center">Loading…</div>
      ) : displaySuites.length === 0 ? (
        <div className="flex flex-col items-center py-10 gap-3 text-center">
          <p className="text-sm text-gray-400">
            {search || statusFilter !== 'all' ? 'No suites match your filters.' : 'No test suites yet.'}
          </p>
          {!search && statusFilter === 'all' && (
            <button
              onClick={handleOpenCreate}
              className="text-sm text-[#fc0101] border border-[#fc0101] px-4 py-1.5 rounded hover:bg-red-50 cursor-pointer"
            >
              Create your first test suite
            </button>
          )}
        </div>
      ) : (
        <>
          <DynamicTable
            data={displaySuites}
            columns={columns}
            actions={actions}
            getRowKey={(s) => s.id}
          />
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            itemsPerPage={limit}
            totalItems={totalItems}
            onPageChange={setPage}
            onItemsPerPageChange={(val) => { setLimit(val); setPage(1) }}
          />
        </>
      )}

      {/* Builder Dialog */}
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

      {/* Delete Confirm */}
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

      {/* Run Confirm */}
      <ConfirmModal
        open={!!runTarget}
        title="Run Test Suite"
        message={`Run "${runTarget?.title}"? This will execute all ${runTarget?.scenario_count ?? 0} scenarios and ${runTarget?.test_case_count ?? 0} test cases.`}
        confirmText="Run"
        cancelText="Cancel"
        variant="default"
        isLoading={isRunning}
        onConfirm={handleConfirmRun}
        onCancel={() => setRunTarget(null)}
      />

      {/* Execution Result Modal */}
      {resultSuite && (
        <ExecutionResultModal
          suite={resultSuite}
          onClose={() => setResultSuite(null)}
        />
      )}
    </div>
  )
}

export default TestSuite
