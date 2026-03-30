import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  MarkerType,
  type Connection,
  type NodeMouseHandler,
  type EdgeMouseHandler,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { X } from 'lucide-react'
import { useGetSiteAttributes } from '@/utils/queries/siteAttributeQuery'
import { useQuery } from '@tanstack/react-query'
import { siteApi } from '@/utils/apis/siteApi'
import api from '@/utils/axios'
import type { FlowDefinition, FlowNodeData } from '@/types/testSuite'

import { nodeTypes } from './nodeTypes'
import { EdgeConditionModal } from './EdgeConditionModal'
import { NodeInfoPanel } from './NodeInfoPanel'
import { SelectionPanel } from './SelectionPanel'
import { START_NODE, buildAutoLayout, buildSequentialEdges } from './helpers'
import type { TestSuiteBuilderProps, PageItem, ScenarioItem, TestCaseItem } from './types'

const TestSuiteBuilder: React.FC<TestSuiteBuilderProps> = ({
  siteId,
  editSuite,
  onClose,
  onSave,
  isSaving,
}) => {
  // ── Form ──────────────────────────────────────────────────────────────────
  const [title, setTitle] = useState(editSuite?.title || '')
  const [description, setDescription] = useState(editSuite?.description || '')

  // ── Selection tree ────────────────────────────────────────────────────────
  const [expandedPages, setExpandedPages] = useState<Set<number>>(new Set())
  const [expandedScenarios, setExpandedScenarios] = useState<Set<number>>(new Set())
  const [selectedScenarioIds, setSelectedScenarioIds] = useState<number[]>([])
  const [checkedTestCases, setCheckedTestCases] = useState<Record<number, number[]>>({})
  const [scenarioTestCases, setScenarioTestCases] = useState<Record<number, TestCaseItem[]>>({})
  const [loadingTCs, setLoadingTCs] = useState<Set<number>>(new Set())
  const [pageScenarios, setPageScenarios] = useState<Record<number, ScenarioItem[]>>({})
  const [loadingScenarios, setLoadingScenarios] = useState<Set<number>>(new Set())
  const [pageSearch, setPageSearch] = useState('')

  // ── Suite reference picker ────────────────────────────────────────────────
  const [leftTab, setLeftTab] = useState<'pages' | 'suites'>('pages')
  const [selectedSuiteRefIds, setSelectedSuiteRefIds] = useState<number[]>([])

  // ── Flow ──────────────────────────────────────────────────────────────────
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([START_NODE])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [edgeModal, setEdgeModal] = useState<Edge | null>(null)
  const [branchLabelInput, setBranchLabelInput] = useState('')
  const [endLabelInput, setEndLabelInput] = useState('')

  // ── Data queries ──────────────────────────────────────────────────────────
  const { data: pagesData } = useQuery({
    queryKey: ['site-pages-all', siteId],
    queryFn: () => siteApi.getPagesBySite({ siteId, page: 1, limit: 100 }),
    enabled: !!siteId,
  })

  const { data: attrData, isLoading: isAttrsLoading } = useGetSiteAttributes(siteId)
  const siteAttributes = useMemo(() => attrData?.items ?? [], [attrData])

  const { data: suitesData } = useQuery({
    queryKey: ['test-suites', siteId],
    queryFn: () => import('@/utils/apis/testSuiteApi').then(m => m.testSuiteApi.listTestSuites(siteId)),
    enabled: !!siteId,
  })

  // Memoised to prevent new array references causing infinite effect loops
  const otherSuites = useMemo(
    () => (suitesData?.items ?? []).filter(s => s.id !== editSuite?.id),
    [suitesData, editSuite?.id],
  )
  const pages = useMemo<PageItem[]>(() => pagesData?.data ?? [], [pagesData])

  // ── Stable load helpers (use refs to avoid re-creating callbacks) ──────────
  const pageScenariosRef = useRef(pageScenarios)
  pageScenariosRef.current = pageScenarios

  const scenarioTestCasesRef = useRef(scenarioTestCases)
  scenarioTestCasesRef.current = scenarioTestCases

  const loadTestCases = useCallback(async (scenarioId: number) => {
    if (scenarioTestCasesRef.current[scenarioId]) return
    setLoadingTCs(prev => new Set(prev).add(scenarioId))
    try {
      const { data } = await api.get('/test-cases', { params: { scenario_id: scenarioId } })
      const tcs: TestCaseItem[] = data
      setScenarioTestCases(prev => ({ ...prev, [scenarioId]: tcs }))
      setCheckedTestCases(prev => ({
        ...prev,
        [scenarioId]: prev[scenarioId] ?? tcs.map(tc => tc.id),
      }))
    } finally {
      setLoadingTCs(prev => { const s = new Set(prev); s.delete(scenarioId); return s })
    }
  }, [])

  const loadScenarios = useCallback(async (pageId: number) => {
    if (pageScenariosRef.current[pageId]) return
    setLoadingScenarios(prev => new Set(prev).add(pageId))
    try {
      const { data } = await api.get('/scenarios', { params: { page_id: pageId, limit: 100 } })
      setPageScenarios(prev => ({ ...prev, [pageId]: data.data || [] }))
    } finally {
      setLoadingScenarios(prev => { const s = new Set(prev); s.delete(pageId); return s })
    }
  }, [])

  // ── Toggle handlers ───────────────────────────────────────────────────────
  const togglePage = (pageId: number) => {
    setExpandedPages(prev => {
      const next = new Set(prev)
      if (next.has(pageId)) { next.delete(pageId) } else { next.add(pageId); loadScenarios(pageId) }
      return next
    })
  }

  const toggleScenario = (scId: number) => {
    setExpandedScenarios(prev => {
      const next = new Set(prev)
      if (next.has(scId)) { next.delete(scId) } else { next.add(scId); loadTestCases(scId) }
      return next
    })
  }

  const toggleScenarioSelection = (scId: number) => {
    setSelectedScenarioIds(prev =>
      prev.includes(scId) ? prev.filter(id => id !== scId) : [...prev, scId]
    )
    loadTestCases(scId)
  }

  const toggleTestCase = (scenarioId: number, tcId: number) => {
    setCheckedTestCases(prev => {
      const curr = prev[scenarioId] || []
      return {
        ...prev,
        [scenarioId]: curr.includes(tcId) ? curr.filter(id => id !== tcId) : [...curr, tcId],
      }
    })
  }

  const toggleSuiteRef = (suiteId: number) => {
    setSelectedSuiteRefIds(prev =>
      prev.includes(suiteId) ? prev.filter(id => id !== suiteId) : [...prev, suiteId]
    )
  }

  // ── Initialise from editSuite ─────────────────────────────────────────────
  useEffect(() => {
    if (!editSuite?.flow_definition) return
    const { nodes: fn, edges: fe } = editSuite.flow_definition
    if (fn?.length) {
      setNodes(fn as Node[])

      const scIds = fn
        .filter(n => n.type === 'step' && n.data.node_reference_type === 'test_scenario')
        .map(n => n.data.node_reference_id as number)
        .filter(Boolean)
      setSelectedScenarioIds(scIds)

      const tcMap: Record<number, number[]> = {}
      fn.forEach(n => {
        if (n.type === 'step' && n.data.node_reference_type === 'test_scenario' && n.data.test_case_ids) {
          tcMap[n.data.node_reference_id as number] = n.data.test_case_ids as number[]
        }
      })
      setCheckedTestCases(tcMap)

      const suiteIds = fn
        .filter(n => n.type === 'suite-ref')
        .map(n => n.data.node_reference_id as number)
        .filter(Boolean)
      setSelectedSuiteRefIds(suiteIds)
    }
    if (fe?.length) {
      setEdges(fe.map(e => ({
        ...(e as unknown as Edge),
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: '#E4D7D7', strokeWidth: 2 },
      })))
    }
  }, [editSuite])

  // ── Auto-rebuild flow when selection changes (create mode only) ───────────
  useEffect(() => {
    if (editSuite) return

    const stepNodes: Node[] = selectedScenarioIds.map((scId, i) => {
      const sc = Object.values(pageScenarios).flat().find(s => s.id === scId)
      const pg = pages.find(p => p.id === sc?.page_id)
      return {
        id: `node-sc-${scId}`,
        type: 'step',
        position: { x: 300, y: (i + 1) * 160 },
        data: {
          label: pg?.page_title || pg?.page_url || 'Page',
          node_type: 'step',
          node_reference_type: 'test_scenario',
          node_reference_id: scId,
          page_id: sc?.page_id,
          scenario_id: scId,
          scenario_title: sc?.title,
          category: sc?.category,
          test_case_ids: checkedTestCases[scId] || [],
        } as FlowNodeData,
      }
    })

    const suiteRefNodes: Node[] = selectedSuiteRefIds.map((sid, i) => {
      const suite = otherSuites.find(s => s.id === sid)
      return {
        id: `node-suite-${sid}`,
        type: 'suite-ref',
        position: { x: 300, y: (selectedScenarioIds.length + i + 1) * 160 },
        data: {
          label: suite?.title || 'Test Suite',
          node_type: 'step',
          node_reference_type: 'test_suite',
          node_reference_id: sid,
          suite_id: sid,
          suite_title: suite?.title,
        } as FlowNodeData,
      }
    })

    const allSteps = [...stepNodes, ...suiteRefNodes]
    const allNodes = [START_NODE, ...buildAutoLayout(allSteps)]
    setNodes(allNodes)
    setEdges(buildSequentialEdges(allNodes))
  }, [selectedScenarioIds, selectedSuiteRefIds, checkedTestCases, pageScenarios, pages, otherSuites, editSuite])

  // ── Derived: scenarios already present as nodes ───────────────────────────
  const scenariosInFlow = useMemo(
    () => new Set(
      nodes
        .filter(n => n.type === 'step' && (n.data as FlowNodeData).node_reference_type === 'test_scenario')
        .map(n => (n.data as FlowNodeData).node_reference_id as number),
    ),
    [nodes],
  )

  // ── Flow interaction handlers ─────────────────────────────────────────────
  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges(eds =>
        addEdge(
          { ...connection, markerEnd: { type: MarkerType.ArrowClosed }, style: { stroke: '#E4D7D7', strokeWidth: 2 } },
          eds,
        ),
      )
    },
    [setEdges],
  )

  const onNodeClick: NodeMouseHandler = useCallback((_event, node) => {
    setSelectedNode(node)
  }, [])

  const onEdgeDoubleClick: EdgeMouseHandler = useCallback((_event, edge) => {
    setEdgeModal(edge)
  }, [])

  const onPaneClick = useCallback(() => setSelectedNode(null), [])

  const handleEdgeConditionSave = (
    edgeId: string,
    label: string,
    condition: { field: string; op: string; value: string } | null,
  ) => {
    setEdges(eds =>
      eds.map(e =>
        e.id === edgeId ? { ...e, label: label || undefined, data: { ...e.data, condition } } : e,
      ),
    )
    setEdgeModal(null)
  }

  // ── Node data update — propagates site_attributes to flow_definition ──────
  const updateNodeData = (nodeId: string, changes: Partial<FlowNodeData>) => {
    setNodes(nds =>
      nds.map(n => (n.id === nodeId ? { ...n, data: { ...n.data, ...changes } } : n)),
    )
    setSelectedNode(prev =>
      prev?.id === nodeId ? { ...prev, data: { ...prev.data, ...changes } } : prev,
    )
  }

  // ── Toolbar actions ───────────────────────────────────────────────────────
  const addBranchNode = () => {
    const label = branchLabelInput.trim() || 'Branch'
    setNodes(prev => [
      ...prev,
      {
        id: `node-branch-${Date.now()}`,
        type: 'branch',
        position: { x: 300, y: prev.length * 160 },
        data: { label, node_type: 'branch' } as FlowNodeData,
      },
    ])
    setBranchLabelInput('')
  }

  const addEndNode = () => {
    const label = endLabelInput.trim() || 'END'
    setNodes(prev => [
      ...prev,
      {
        id: `node-end-${Date.now()}`,
        type: 'end',
        position: { x: 300, y: prev.length * 160 },
        data: { label, node_type: 'end' } as FlowNodeData,
      },
    ])
    setEndLabelInput('')
  }

  const deleteSelectedNode = () => {
    if (!selectedNode) return
    setNodes(nds => nds.filter(n => n.id !== selectedNode.id))
    setEdges(eds => eds.filter(e => e.source !== selectedNode.id && e.target !== selectedNode.id))
    setSelectedNode(null)
  }

  // ── Counts and serialization ──────────────────────────────────────────────
  const scenarioCount = useMemo(
    () => nodes.filter(n => n.type === 'step' || n.type === 'suite-ref').length,
    [nodes],
  )
  const testCaseCount = useMemo(
    () => Object.values(checkedTestCases).reduce((sum, arr) => sum + arr.length, 0),
    [checkedTestCases],
  )

  const getFlowDefinition = (): FlowDefinition => ({
    nodes: nodes.map(n => ({
      id: n.id,
      type: n.type as string,
      position: n.position,
      data: n.data as FlowNodeData,
    })),
    edges: edges.map(e => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: (e.label as string) || null,
      condition: (e.data as any)?.condition || null,
    })),
  })

  const handleSave = () => {
    if (!title.trim()) return
    onSave({
      title: title.trim(),
      description: description.trim(),
      status: 'ready',
      flow_definition: getFlowDefinition(),
      scenario_count: scenarioCount,
      test_case_count: testCaseCount,
    })
  }

  // ── Filtered pages ────────────────────────────────────────────────────────
  const filteredPages = pages.filter(p => {
    const q = pageSearch.toLowerCase()
    return !q || (p.page_title || p.page_url).toLowerCase().includes(q)
  })

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-[1200px] h-[92vh] flex flex-col">

        {/* Header */}
        <div className="bg-[#FFF8F8] border-b border-[#E4D7D7] px-5 py-3 flex items-center gap-4 rounded-t-xl">
          <div className="flex-1 flex gap-3 items-center">
            <input
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Suite title *"
              className="font-semibold text-sm border border-[#E4D7D7] rounded px-3 py-1.5 w-56 focus:outline-none focus:ring-1 focus:ring-[#fc0101]"
            />
            <input
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Description"
              className="text-sm border border-[#E4D7D7] rounded px-3 py-1.5 flex-1 focus:outline-none focus:ring-1 focus:ring-[#fc0101]"
            />
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left: Selection Panel */}
          <SelectionPanel
            leftTab={leftTab}
            setLeftTab={setLeftTab}
            pageSearch={pageSearch}
            setPageSearch={setPageSearch}
            filteredPages={filteredPages}
            pageScenarios={pageScenarios}
            loadingScenarios={loadingScenarios}
            expandedPages={expandedPages}
            togglePage={togglePage}
            expandedScenarios={expandedScenarios}
            toggleScenario={toggleScenario}
            selectedScenarioIds={selectedScenarioIds}
            scenariosInFlow={scenariosInFlow}
            toggleScenarioSelection={toggleScenarioSelection}
            scenarioTestCases={scenarioTestCases}
            loadingTCs={loadingTCs}
            checkedTestCases={checkedTestCases}
            toggleTestCase={toggleTestCase}
            otherSuites={otherSuites}
            selectedSuiteRefIds={selectedSuiteRefIds}
            toggleSuiteRef={toggleSuiteRef}
            selectedNode={selectedNode}
            branchLabelInput={branchLabelInput}
            setBranchLabelInput={setBranchLabelInput}
            addBranchNode={addBranchNode}
            endLabelInput={endLabelInput}
            setEndLabelInput={setEndLabelInput}
            addEndNode={addEndNode}
            deleteSelectedNode={deleteSelectedNode}
          />

          {/* Right: Flow Canvas */}
          <div className="flex-1 relative bg-[#fafafa]">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onEdgeDoubleClick={onEdgeDoubleClick}
              onPaneClick={onPaneClick}
              nodeTypes={nodeTypes}
              fitView
              fitViewOptions={{ padding: 0.3 }}
              className="rounded-br-xl"
            >
              <Background color="#E4D7D7" gap={20} size={1} />
              <Controls className="!border-[#E4D7D7]" />
              <MiniMap
                nodeColor={n => {
                  if (n.type === 'start') return '#10b981'
                  if (n.type === 'end') return '#fc0101'
                  if (n.type === 'branch') return '#f59e0b'
                  if (n.type === 'suite-ref') return '#3b82f6'
                  return '#fff'
                }}
                className="!border-[#E4D7D7] !bg-white"
              />
            </ReactFlow>

            <div className="absolute top-3 right-3 bg-white border border-[#E4D7D7] rounded px-2 py-1 text-[10px] text-gray-400 shadow-sm">
              Double-click edge to set condition · Drag to reorder nodes · Click node to set attributes
            </div>

            {selectedNode && (
              <NodeInfoPanel
                node={selectedNode}
                siteAttributes={siteAttributes}
                isAttrsLoading={isAttrsLoading}
                onUpdate={updateNodeData}
                onClose={() => setSelectedNode(null)}
              />
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-[#E4D7D7] bg-white px-5 py-3 flex items-center justify-between rounded-b-xl">
          <div className="text-xs text-gray-400 space-x-3">
            <span>{nodes.filter(n => n.type === 'step' || n.type === 'suite-ref').length} step nodes</span>
            <span>{testCaseCount} test cases</span>
            <span>{edges.length} connections</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="text-sm border border-[#E4D7D7] rounded px-4 py-1.5 cursor-pointer hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!title.trim() || isSaving}
              className="text-sm bg-[#fc0101] text-white rounded px-5 py-1.5 cursor-pointer hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'Saving…' : editSuite ? 'Update Suite' : 'Create Suite'}
            </button>
          </div>
        </div>
      </div>

      {edgeModal && (
        <EdgeConditionModal
          edge={edgeModal}
          onSave={handleEdgeConditionSave}
          onClose={() => setEdgeModal(null)}
        />
      )}
    </div>
  )
}

export default TestSuiteBuilder
