import { Handle, Position } from '@xyflow/react'
import type { FlowNodeData } from '@/types/testSuite'

// ─── Start Node ───────────────────────────────────────────────────────────────

export const StartNode = ({ data }: { data: FlowNodeData }) => (
  <div className="px-5 py-2 rounded-full bg-emerald-500 text-white text-xs font-semibold shadow border-2 border-emerald-600 min-w-[80px] text-center">
    {data.label}
    <Handle type="source" position={Position.Bottom} style={{ background: '#10b981', border: '2px solid #fff' }} />
  </div>
)

// ─── End Node ─────────────────────────────────────────────────────────────────

export const EndNode = ({ data }: { data: FlowNodeData }) => (
  <div className="px-5 py-2 rounded-full bg-[#fc0101] text-white text-xs font-semibold shadow border-2 border-red-700 min-w-[80px] text-center">
    <Handle type="target" position={Position.Top} style={{ background: '#fc0101', border: '2px solid #fff' }} />
    {data.label}
  </div>
)

// ─── Step Node (Test Scenario) ────────────────────────────────────────────────

export const StepNode = ({ data, selected }: { data: FlowNodeData; selected?: boolean }) => {
  const tcCount = (data.test_case_ids as number[] | undefined)?.length ?? 0
  const attrs = (data.site_attributes as Array<{ key: string; value: string }> | undefined) ?? []

  return (
    <div
      className={`bg-white rounded-lg shadow border-l-4 border-l-[#fc0101] min-w-[190px] max-w-[230px] text-xs transition-all ${
        selected ? 'ring-2 ring-[#fc0101] ring-offset-1' : 'border border-[#E4D7D7]'
      }`}
    >
      <Handle type="target" position={Position.Top} style={{ background: '#fc0101', border: '2px solid #fff' }} />

      {/* Header */}
      <div className="bg-[#FFF8F8] px-3 py-1.5 rounded-tl-md rounded-tr-[6px] border-b border-[#E4D7D7]">
        <div className="flex items-start justify-between gap-1">
          <p className="font-semibold text-[#333] truncate flex-1 leading-snug">
            {data.scenario_title || data.label}
          </p>
          {/* Blue dot indicator — shown when node has site attributes */}
          {attrs.length > 0 && (
            <span
              className="shrink-0 mt-0.5 w-2.5 h-2.5 rounded-full bg-blue-500 block border-2 border-blue-200"
              title={attrs.map(a => `${a.key}: ${a.value}`).join('\n')}
            />
          )}
        </div>
      </div>

      {/* Footer badges */}
      <div className="px-3 py-1.5 flex items-center gap-1.5 flex-wrap">
        {data.category && (
          <span className="text-[9px] bg-[#f6f3f3] text-gray-500 rounded px-1.5 py-0.5 border border-[#E4D7D7]">
            {data.category}
          </span>
        )}
        {tcCount > 0 && (
          <span className="text-[9px] bg-red-50 text-[#fc0101] rounded px-1.5 py-0.5 border border-red-200 ml-auto">
            {tcCount} TC
          </span>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} style={{ background: '#fc0101', border: '2px solid #fff' }} />
    </div>
  )
}

// ─── Branch Node ──────────────────────────────────────────────────────────────

export const BranchNode = ({ data, selected }: { data: FlowNodeData; selected?: boolean }) => (
  <div
    className={`relative flex items-center justify-center w-[120px] h-[50px] rotate-45 bg-amber-100 border-2 border-amber-400 shadow transition-all ${
      selected ? 'ring-2 ring-amber-400 ring-offset-1' : ''
    }`}
  >
    <Handle type="target" position={Position.Top} style={{ background: '#f59e0b', border: '2px solid #fff', top: -6 }} />
    <span className="-rotate-45 text-[10px] font-semibold text-amber-700 text-center px-2">
      {data.label}
    </span>
    <Handle type="source" position={Position.Bottom} id="bottom" style={{ background: '#f59e0b', border: '2px solid #fff', bottom: -6 }} />
    <Handle type="source" position={Position.Left} id="left" style={{ background: '#f59e0b', border: '2px solid #fff', left: -6 }} />
    <Handle type="source" position={Position.Right} id="right" style={{ background: '#f59e0b', border: '2px solid #fff', right: -6 }} />
  </div>
)

// ─── Suite Reference Node ─────────────────────────────────────────────────────

export const SuiteRefNode = ({ data, selected }: { data: FlowNodeData; selected?: boolean }) => {
  const attrs = (data.site_attributes as Array<{ key: string; value: string }> | undefined) ?? []

  return (
    <div
      className={`bg-blue-50 rounded-lg shadow border-l-4 border-l-blue-500 min-w-[190px] max-w-[230px] text-xs transition-all ${
        selected ? 'ring-2 ring-blue-400 ring-offset-1' : 'border border-blue-200'
      }`}
    >
      <Handle type="target" position={Position.Top} style={{ background: '#3b82f6', border: '2px solid #fff' }} />

      <div className="bg-blue-50 px-3 py-1.5 rounded-t-md border-b border-blue-200">
        <div className="flex items-start justify-between gap-1">
          <p className="font-semibold text-blue-700 truncate flex-1">{data.label}</p>
          {/* Blue dot indicator for site attributes */}
          {attrs.length > 0 && (
            <span
              className="shrink-0 mt-0.5 w-2.5 h-2.5 rounded-full bg-blue-500 block border-2 border-blue-200"
              title={attrs.map(a => `${a.key}: ${a.value}`).join('\n')}
            />
          )}
        </div>
      </div>

      <div className="px-3 py-1.5">
        <span className="text-[9px] bg-blue-100 text-blue-600 rounded px-1.5 py-0.5">
          Suite Reference
        </span>
      </div>

      <Handle type="source" position={Position.Bottom} style={{ background: '#3b82f6', border: '2px solid #fff' }} />
    </div>
  )
}

// ─── Node Types Map ────────────────────────────────────────────────────────────

export const nodeTypes = {
  start: StartNode,
  end: EndNode,
  step: StepNode,
  branch: BranchNode,
  'suite-ref': SuiteRefNode,
} as const
