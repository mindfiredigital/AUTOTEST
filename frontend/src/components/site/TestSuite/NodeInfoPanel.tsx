import React, { useEffect, useState } from 'react'
import { X, Plus } from 'lucide-react'
import type { Node } from '@xyflow/react'
import type { FlowNodeData } from '@/types/testSuite'

interface SiteAttributeOption {
  id: number
  attribute_key: string
  attribute_title: string
}

interface NodeInfoPanelProps {
  node: Node | null
  siteAttributes: SiteAttributeOption[]
  isAttrsLoading?: boolean
  onUpdate: (nodeId: string, changes: Partial<FlowNodeData>) => void
  onClose: () => void
}

export const NodeInfoPanel: React.FC<NodeInfoPanelProps> = ({
  node,
  siteAttributes,
  isAttrsLoading,
  onUpdate,
  onClose,
}) => {
  const data = node?.data as FlowNodeData | undefined
  const [attrs, setAttrs] = useState<Array<{ key: string; value: string }>>([])
  const [newKey, setNewKey] = useState('')
  const [newValue, setNewValue] = useState('')

  // Re-initialise when switching to a different node
  useEffect(() => {
    setAttrs((data?.site_attributes as Array<{ key: string; value: string }> | undefined) ?? [])
    setNewKey('')
    setNewValue('')
  }, [node?.id])

  if (!node || !data || data.node_type === 'start' || data.node_type === 'end') return null

  const addAttr = () => {
    if (!newKey) return
    // Upsert: replace existing entry with the same key, otherwise append
    const updated = attrs.filter(a => a.key !== newKey).concat({ key: newKey, value: newValue })
    setAttrs(updated)
    onUpdate(node.id, { site_attributes: updated })
    setNewKey('')
    setNewValue('')
  }

  const removeAttr = (key: string) => {
    const updated = attrs.filter(a => a.key !== key)
    setAttrs(updated)
    onUpdate(node.id, { site_attributes: updated })
  }

  return (
    <div className="absolute bottom-0 left-0 right-0 bg-white border-t border-[#E4D7D7] z-10 shadow-lg rounded-b-lg">
      {/* Panel header */}
      <div className="flex items-center justify-between bg-[#FFF8F8] border-b border-[#E4D7D7] px-4 py-2">
        <h4 className="text-xs font-semibold text-[#333] truncate max-w-[60%]">
          {data.scenario_title || data.suite_title || data.label}
        </h4>
        <div className="flex items-center gap-3">
          {data.node_reference_type === 'test_scenario' && (
            <span className="text-[10px] text-gray-400">
              {(data.test_case_ids as number[] | undefined)?.length ?? 0} test cases ·{' '}
              <span className="text-[#8B6E6E]">{data.category}</span>
            </span>
          )}
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 cursor-pointer">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="px-4 py-3 text-xs">
        {/* Section label */}
        <p className="text-[10px] text-[#8B6E6E] font-medium mb-1.5">
          Site Attributes
          {attrs.length > 0 && <span className="ml-1 text-blue-500">({attrs.length})</span>}
        </p>

        {/* Applied attributes */}
        {attrs.length > 0 && (
          <div className="mb-2 space-y-1">
            {attrs.map(a => (
              <div
                key={a.key}
                className="flex items-center gap-2 bg-blue-50 border border-blue-100 rounded px-2 py-1"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                <span className="text-[10px] text-blue-700 font-medium shrink-0">{a.key}</span>
                <span className="text-[10px] text-gray-400">:</span>
                <span className="text-[10px] text-gray-700 flex-1 truncate">{a.value || '—'}</span>
                <button
                  onClick={() => removeAttr(a.key)}
                  className="text-red-400 hover:text-red-600 cursor-pointer shrink-0"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Add row */}
        <div className="flex gap-1.5 items-center">
          <select
            value={newKey}
            onChange={e => setNewKey(e.target.value)}
            disabled={isAttrsLoading}
            className="flex-1 border border-[#E4D7D7] rounded px-2 py-1 text-[10px] focus:outline-none focus:ring-1 focus:ring-[#fc0101] min-w-0 disabled:opacity-60"
          >
            <option value="">
              {isAttrsLoading
                ? 'Loading attributes…'
                : siteAttributes.length === 0
                  ? 'No attributes defined'
                  : 'Select attribute key…'}
            </option>
            {siteAttributes
              .filter(a => !attrs.some(ex => ex.key === a.attribute_key))
              .map(a => (
                <option key={a.id} value={a.attribute_key}>
                  {a.attribute_key}
                  {a.attribute_title ? ` — ${a.attribute_title}` : ''}
                </option>
              ))}
          </select>
          <input
            value={newValue}
            onChange={e => setNewValue(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addAttr()}
            placeholder="value"
            className="w-24 border border-[#E4D7D7] rounded px-2 py-1 text-[10px] focus:outline-none focus:ring-1 focus:ring-[#fc0101]"
          />
          <button
            onClick={addAttr}
            disabled={!newKey}
            className="bg-[#fc0101] text-white rounded px-2 py-1 cursor-pointer hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  )
}
