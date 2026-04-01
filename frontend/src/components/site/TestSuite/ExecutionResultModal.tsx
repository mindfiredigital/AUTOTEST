import React from 'react'
import { X, CheckCircle2, XCircle, SkipForward, Hash, Clock, Calendar } from 'lucide-react'
import { useExecutionResultQuery } from '@/utils/queries/testSuiteQueries'
import type { TestSuite } from '@/types/testSuite'

interface ExecutionResultModalProps {
  suite: TestSuite
  onClose: () => void
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; border: string }> = {
  passed:           { label: 'Passed',           color: 'text-emerald-600', bg: 'bg-emerald-50',  border: 'border-emerald-200' },
  partially_passed: { label: 'Partially Passed', color: 'text-amber-600',   bg: 'bg-amber-50',    border: 'border-amber-200'   },
  failed:           { label: 'Failed',           color: 'text-[#fc0101]',   bg: 'bg-red-50',      border: 'border-red-200'     },
  running:          { label: 'Running',          color: 'text-blue-600',    bg: 'bg-blue-50',     border: 'border-blue-200'    },
  error:            { label: 'Error',            color: 'text-orange-600',  bg: 'bg-orange-50',   border: 'border-orange-200'  },
  pending:          { label: 'Pending',          color: 'text-gray-500',    bg: 'bg-gray-50',     border: 'border-gray-200'    },
}

export const ExecutionResultModal: React.FC<ExecutionResultModalProps> = ({ suite, onClose }) => {
  const { data: execution, isLoading, isError } = useExecutionResultQuery(suite.id)

  const summary = execution?.execution_summary
  const total   = summary?.total   ?? 0
  const passed  = summary?.passed  ?? 0
  const failed  = summary?.failed  ?? 0
  const skipped = summary?.skipped ?? 0

  const passRate = total > 0 ? Math.round((passed / total) * 100) : 0

  const execStatus = execution?.status ?? 'pending'
  const cfg = STATUS_CONFIG[execStatus] ?? STATUS_CONFIG.pending

  const fmt = (d?: string | null) =>
    d ? new Date(d).toLocaleString() : '—'

  const duration = (() => {
    if (!execution?.started_at || !execution?.ended_at) return null
    const secs = Math.floor(
      (new Date(execution.ended_at).getTime() - new Date(execution.started_at).getTime()) / 1000,
    )
    return secs < 60 ? `${secs}s` : `${Math.floor(secs / 60)}m ${secs % 60}s`
  })()

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">

        {/* ── Header ── */}
        <div className="bg-[#FFF8F8] border-b border-[#E4D7D7] px-5 py-3.5 flex items-center justify-between rounded-t-xl shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <h2 className="text-sm font-semibold text-[#333] truncate">{suite.title}</h2>
            {execution && (
              <span
                className={`shrink-0 text-[10px] font-semibold uppercase px-2 py-0.5 rounded border tracking-wide ${cfg.bg} ${cfg.color} ${cfg.border}`}
              >
                {cfg.label}
              </span>
            )}
          </div>
          <button onClick={onClose} className="ml-4 text-gray-400 hover:text-gray-600 cursor-pointer shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* ── Body ── */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">

          {isLoading && (
            <p className="text-sm text-gray-400 text-center py-10">Loading execution result…</p>
          )}

          {isError && (
            <p className="text-sm text-gray-400 text-center py-10">
              No execution result found for this test suite.
            </p>
          )}

          {execution && (
            <>
              {/* Timing row */}
              <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 shrink-0" />
                  Started: {fmt(execution.started_at)}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 shrink-0" />
                  Ended: {fmt(execution.ended_at)}
                </span>
                {duration && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 shrink-0" />
                    Duration: {duration}
                  </span>
                )}
              </div>

              {/* Summary cards */}
              <div className="grid grid-cols-4 gap-3">
                <SummaryCard
                  label="Total"
                  value={total}
                  color="text-gray-700"
                  bg="bg-gray-50"
                  border="border-gray-200"
                  icon={<Hash className="w-4 h-4" />}
                />
                <SummaryCard
                  label="Passed"
                  value={passed}
                  color="text-emerald-600"
                  bg="bg-emerald-50"
                  border="border-emerald-200"
                  icon={<CheckCircle2 className="w-4 h-4" />}
                />
                <SummaryCard
                  label="Failed"
                  value={failed}
                  color="text-[#fc0101]"
                  bg="bg-red-50"
                  border="border-red-200"
                  icon={<XCircle className="w-4 h-4" />}
                />
                <SummaryCard
                  label="Skipped"
                  value={skipped}
                  color="text-amber-600"
                  bg="bg-amber-50"
                  border="border-amber-200"
                  icon={<SkipForward className="w-4 h-4" />}
                />
              </div>

              {/* Progress bar */}
              {total > 0 && (
                <div>
                  <div className="flex justify-between text-[10px] text-gray-500 mb-1.5">
                    <span>Pass rate</span>
                    <span className="font-semibold">{passRate}%</span>
                  </div>
                  <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden flex">
                    {passed > 0 && (
                      <div
                        className="h-full bg-emerald-400 transition-all"
                        style={{ width: `${(passed / total) * 100}%` }}
                      />
                    )}
                    {failed > 0 && (
                      <div
                        className="h-full bg-[#fc0101] transition-all"
                        style={{ width: `${(failed / total) * 100}%` }}
                      />
                    )}
                    {skipped > 0 && (
                      <div
                        className="h-full bg-amber-300 transition-all"
                        style={{ width: `${(skipped / total) * 100}%` }}
                      />
                    )}
                  </div>
                  <div className="flex gap-4 mt-2 text-[10px] text-gray-500">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
                      Passed
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-[#fc0101] inline-block" />
                      Failed
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-amber-300 inline-block" />
                      Skipped
                    </span>
                  </div>
                </div>
              )}

              {/* Error detail (if any) */}
              {summary?.error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-600">
                  <span className="font-semibold">Error: </span>{summary.error}
                </div>
              )}

              {/* Logs */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Execution Logs
                </h3>
                <div className="bg-gray-950 rounded-lg overflow-auto max-h-72 p-4">
                  <pre className="text-[11px] leading-5 text-gray-300 whitespace-pre-wrap font-mono">
                    {execution.logs?.trim() || 'No logs available.'}
                  </pre>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

const SummaryCard: React.FC<{
  label: string
  value: number
  color: string
  bg: string
  border: string
  icon: React.ReactNode
}> = ({ label, value, color, bg, border, icon }) => (
  <div className={`rounded-lg border ${border} ${bg} p-3 flex flex-col gap-1.5`}>
    <div className={`flex items-center gap-1.5 ${color} text-[11px] font-medium`}>
      {icon}
      {label}
    </div>
    <span className={`text-2xl font-bold ${color}`}>{value}</span>
  </div>
)
