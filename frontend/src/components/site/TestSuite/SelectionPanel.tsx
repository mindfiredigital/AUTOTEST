import React from 'react'
import { ChevronDown, ChevronRight, GitMerge, Flag, Trash2 } from 'lucide-react'
import type { Node } from '@xyflow/react'
import type { PageItem, ScenarioItem, TestCaseItem } from './types'
import type { TestSuite } from '@/types/testSuite'

interface SelectionPanelProps {
  // Tabs
  leftTab: 'pages' | 'suites'
  setLeftTab: (tab: 'pages' | 'suites') => void

  // Page tree
  pageSearch: string
  setPageSearch: (s: string) => void
  filteredPages: PageItem[]
  pageScenarios: Record<number, ScenarioItem[]>
  loadingScenarios: Set<number>
  expandedPages: Set<number>
  togglePage: (pageId: number) => void

  // Scenario selection
  expandedScenarios: Set<number>
  toggleScenario: (scId: number) => void
  selectedScenarioIds: number[]
  scenariosInFlow: Set<number>
  toggleScenarioSelection: (scId: number) => void
  scenarioTestCases: Record<number, TestCaseItem[]>
  loadingTCs: Set<number>
  checkedTestCases: Record<number, number[]>
  toggleTestCase: (scenarioId: number, tcId: number) => void

  // Suite references
  otherSuites: TestSuite[]
  selectedSuiteRefIds: number[]
  toggleSuiteRef: (suiteId: number) => void

  // Toolbar
  selectedNode: Node | null
  branchLabelInput: string
  setBranchLabelInput: (s: string) => void
  addBranchNode: () => void
  endLabelInput: string
  setEndLabelInput: (s: string) => void
  addEndNode: () => void
  deleteSelectedNode: () => void
}

export const SelectionPanel: React.FC<SelectionPanelProps> = ({
  leftTab,
  setLeftTab,
  pageSearch,
  setPageSearch,
  filteredPages,
  pageScenarios,
  loadingScenarios,
  expandedPages,
  togglePage,
  expandedScenarios,
  toggleScenario,
  selectedScenarioIds,
  scenariosInFlow,
  toggleScenarioSelection,
  scenarioTestCases,
  loadingTCs,
  checkedTestCases,
  toggleTestCase,
  otherSuites,
  selectedSuiteRefIds,
  toggleSuiteRef,
  selectedNode,
  branchLabelInput,
  setBranchLabelInput,
  addBranchNode,
  endLabelInput,
  setEndLabelInput,
  addEndNode,
  deleteSelectedNode,
}) => {
  return (
    <div className="w-72 border-r border-[#E4D7D7] flex flex-col bg-white">
      {/* Tabs */}
      <div className="flex border-b border-[#E4D7D7]">
        {(['pages', 'suites'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setLeftTab(tab)}
            className={`flex-1 py-2 text-xs font-medium capitalize cursor-pointer transition-colors ${
              leftTab === tab
                ? 'border-b-2 border-[#fc0101] text-[#fc0101]'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'pages' ? 'Pages & Scenarios' : 'Test Suites'}
          </button>
        ))}
      </div>

      {/* Pages & Scenarios tab */}
      {leftTab === 'pages' && (
        <>
          <div className="px-3 py-2 border-b border-[#E4D7D7]">
            <input
              value={pageSearch}
              onChange={e => setPageSearch(e.target.value)}
              placeholder="Search pages..."
              className="w-full border border-[#E4D7D7] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-[#fc0101]"
            />
          </div>

          <div className="flex-1 overflow-y-auto hide-scrollbar">
            {filteredPages.length === 0 ? (
              <p className="text-xs text-gray-400 p-4 text-center">No pages found</p>
            ) : (
              filteredPages.map(page => {
                const scenarios = pageScenarios[page.id] || []
                const isExpanded = expandedPages.has(page.id)
                const isLoading = loadingScenarios.has(page.id)

                return (
                  <div key={page.id} className="border-b border-[#F5EDED]">
                    {/* Page row */}
                    <button
                      onClick={() => togglePage(page.id)}
                      className="w-full flex items-center gap-2 px-3 py-2.5 hover:bg-[#FFF8F8] text-left cursor-pointer"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                      )}
                      <span className="text-xs font-medium text-[#333] truncate flex-1">
                        {page.page_title || page.page_url}
                      </span>
                    </button>

                    {/* Scenarios */}
                    {isExpanded && (
                      <div className="pl-5">
                        {isLoading ? (
                          <p className="text-[10px] text-gray-400 px-3 py-2">Loading…</p>
                        ) : scenarios.length === 0 ? (
                          <p className="text-[10px] text-gray-400 px-3 py-2">No scenarios</p>
                        ) : (
                          scenarios.map(sc => {
                            const isScSelected = selectedScenarioIds.includes(sc.id)
                            const isScExpanded = expandedScenarios.has(sc.id)
                            const tcs = scenarioTestCases[sc.id] || []
                            const isTCLoading = loadingTCs.has(sc.id)
                            const alreadyInFlow = scenariosInFlow.has(sc.id) && !isScSelected

                            return (
                              <div key={sc.id} className="border-l-2 border-[#F5EDED] ml-1">
                                {/* Scenario row */}
                                <div className={`flex items-center gap-1.5 px-2 py-2 hover:bg-[#FFF8F8] ${alreadyInFlow ? 'opacity-40' : ''}`}>
                                  <input
                                    type="checkbox"
                                    checked={isScSelected}
                                    disabled={alreadyInFlow}
                                    onChange={() => toggleScenarioSelection(sc.id)}
                                    className="accent-[#fc0101] cursor-pointer shrink-0 disabled:cursor-not-allowed"
                                  />
                                  <button
                                    onClick={() => toggleScenario(sc.id)}
                                    className="flex items-center gap-1 flex-1 text-left cursor-pointer"
                                  >
                                    {isScExpanded ? (
                                      <ChevronDown className="w-3 h-3 text-gray-400 shrink-0" />
                                    ) : (
                                      <ChevronRight className="w-3 h-3 text-gray-400 shrink-0" />
                                    )}
                                    <span className="text-[11px] text-[#444] truncate">{sc.title}</span>
                                  </button>
                                  {isScSelected && (
                                    <span className="text-[8px] bg-emerald-50 text-emerald-600 border border-emerald-200 rounded px-1 shrink-0">
                                      in flow
                                    </span>
                                  )}
                                </div>

                                {/* Test Cases */}
                                {isScExpanded && (
                                  <div className="pl-6 pb-1">
                                    {isTCLoading ? (
                                      <p className="text-[10px] text-gray-400 py-1">Loading…</p>
                                    ) : tcs.length === 0 ? (
                                      <p className="text-[10px] text-gray-400 py-1">No test cases</p>
                                    ) : (
                                      tcs.map(tc => (
                                        <label
                                          key={tc.id}
                                          className="flex items-center gap-1.5 py-1 cursor-pointer hover:bg-[#FFF8F8] px-1 rounded"
                                        >
                                          <input
                                            type="checkbox"
                                            checked={(checkedTestCases[sc.id] || []).includes(tc.id)}
                                            onChange={() => toggleTestCase(sc.id, tc.id)}
                                            className="accent-[#fc0101] cursor-pointer shrink-0"
                                          />
                                          <span className="text-[10px] text-gray-500 truncate">{tc.title}</span>
                                        </label>
                                      ))
                                    )}
                                  </div>
                                )}
                              </div>
                            )
                          })
                        )}
                      </div>
                    )}
                  </div>
                )
              })
            )}
          </div>
        </>
      )}

      {/* Test Suites tab */}
      {leftTab === 'suites' && (
        <div className="flex-1 overflow-y-auto hide-scrollbar p-2">
          <p className="text-[10px] text-gray-400 px-2 py-1 mb-1">Select suites to reference as nodes</p>
          {otherSuites.length === 0 ? (
            <p className="text-xs text-gray-400 p-3 text-center">No other suites</p>
          ) : (
            otherSuites.map(s => (
              <label
                key={s.id}
                className="flex items-center gap-2 px-3 py-2.5 hover:bg-[#FFF8F8] border-b border-[#F5EDED] cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedSuiteRefIds.includes(s.id)}
                  onChange={() => toggleSuiteRef(s.id)}
                  className="accent-[#fc0101] cursor-pointer"
                />
                <div>
                  <p className="text-xs font-medium text-[#333]">{s.title}</p>
                  <p className="text-[10px] text-gray-400">{s.scenario_count ?? 0} scenarios</p>
                </div>
              </label>
            ))
          )}
        </div>
      )}

      {/* Flow toolbar */}
      <div className="border-t border-[#E4D7D7] p-2 space-y-1.5">
        <p className="text-[10px] text-gray-400 px-1 font-medium">Add Nodes</p>

        <div className="flex gap-1.5">
          <input
            value={branchLabelInput}
            onChange={e => setBranchLabelInput(e.target.value)}
            placeholder="Branch label"
            className="flex-1 border border-[#E4D7D7] rounded px-2 py-1 text-[10px] focus:outline-none focus:ring-1 focus:ring-amber-400"
          />
          <button
            onClick={addBranchNode}
            title="Add Branch"
            className="bg-amber-100 text-amber-700 border border-amber-300 rounded px-2 py-1 cursor-pointer hover:bg-amber-200"
          >
            <GitMerge className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="flex gap-1.5">
          <input
            value={endLabelInput}
            onChange={e => setEndLabelInput(e.target.value)}
            placeholder="End label"
            className="flex-1 border border-[#E4D7D7] rounded px-2 py-1 text-[10px] focus:outline-none focus:ring-1 focus:ring-red-400"
          />
          <button
            onClick={addEndNode}
            title="Add End"
            className="bg-red-50 text-[#fc0101] border border-red-300 rounded px-2 py-1 cursor-pointer hover:bg-red-100"
          >
            <Flag className="w-3.5 h-3.5" />
          </button>
        </div>

        {selectedNode && !['start'].includes(selectedNode.data.node_type as string) && (
          <button
            onClick={deleteSelectedNode}
            className="w-full flex items-center justify-center gap-1.5 text-[10px] text-red-500 border border-red-200 rounded px-2 py-1 hover:bg-red-50 cursor-pointer"
          >
            <Trash2 className="w-3 h-3" />
            Delete selected node
          </button>
        )}
      </div>
    </div>
  )
}
