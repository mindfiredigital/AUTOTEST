import React, { useState } from 'react'
import { X } from 'lucide-react'
import type { Edge } from '@xyflow/react'

interface EdgeConditionModalProps {
  edge: Edge | null
  onSave: (edgeId: string, label: string, condition: { field: string; op: string; value: string } | null) => void
  onClose: () => void
}

export const EdgeConditionModal: React.FC<EdgeConditionModalProps> = ({ edge, onSave, onClose }) => {
  const [label, setLabel] = useState(edge?.label as string || '')
  const [field, setField] = useState((edge?.data as any)?.condition?.field || '')
  const [op, setOp] = useState((edge?.data as any)?.condition?.op || 'eq')
  const [value, setValue] = useState((edge?.data as any)?.condition?.value || '')

  if (!edge) return null

  const handleSave = () => {
    const condition = field ? { field, op, value } : null
    onSave(edge.id, label, condition)
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-[400px]">
        <div className="flex items-center justify-between border-b px-5 py-3">
          <h3 className="font-semibold text-sm">Edge Condition</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-3">
          <div>
            <label className="text-[11px] text-[#8B6E6E] font-medium">Label</label>
            <input
              value={label}
              onChange={e => setLabel(e.target.value)}
              placeholder="e.g. Login passed"
              className="mt-1 w-full border border-[#E4D7D7] rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[#fc0101]"
            />
          </div>

          <p className="text-[10px] text-gray-400 font-medium uppercase tracking-wide">Condition (optional)</p>

          <div className="flex gap-2">
            <input
              value={field}
              onChange={e => setField(e.target.value)}
              placeholder="field (e.g. _outcome)"
              className="flex-1 border border-[#E4D7D7] rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-[#fc0101]"
            />
            <select
              value={op}
              onChange={e => setOp(e.target.value)}
              className="border border-[#E4D7D7] rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-[#fc0101]"
            >
              <option value="eq">eq</option>
              <option value="neq">neq</option>
              <option value="gt">gt</option>
              <option value="lt">lt</option>
              <option value="contains">contains</option>
            </select>
            <input
              value={value}
              onChange={e => setValue(e.target.value)}
              placeholder="value"
              className="flex-1 border border-[#E4D7D7] rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-[#fc0101]"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 border-t px-5 py-3">
          <button
            onClick={onClose}
            className="text-sm border border-gray-300 rounded px-4 py-1.5 cursor-pointer hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="text-sm bg-[#fc0101] text-white rounded px-4 py-1.5 cursor-pointer hover:bg-red-700"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  )
}
