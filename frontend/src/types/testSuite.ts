// ─── Flow definition types (stored in flow_definition JSON) ───────────────────

export type NodeReferenceType = 'test_scenario' | 'test_suite'
export type NodeType = 'start' | 'step' | 'branch' | 'end'

export interface FlowNodeData {
  label: string
  node_type: NodeType
  node_reference_type?: NodeReferenceType
  node_reference_id?: number
  page_id?: number | null
  scenario_id?: number | null
  suite_id?: number | null
  page_title?: string
  scenario_title?: string
  suite_title?: string
  category?: string
  site_attributes?: Array<{ key: string; value: string }>
  test_case_ids?: number[]
  [key: string]: unknown
}

export interface FlowNode {
  id: string
  type: string
  position: { x: number; y: number }
  data: FlowNodeData
}

export interface EdgeCondition {
  field: string
  op: string
  value: string
}

export interface FlowEdge {
  id: string
  source: string
  target: string
  label?: string | null
  condition?: EdgeCondition | null
}

export interface FlowDefinition {
  nodes: FlowNode[]
  edges: FlowEdge[]
}

// ─── API types ─────────────────────────────────────────────────────────────────

export type TestSuiteStatus = 'draft' | 'ready' | 'running' | 'done' | 'failed'

export interface TestSuite {
  id: number
  site_id: number
  title: string
  description?: string
  status: TestSuiteStatus
  flow_definition: FlowDefinition
  scenario_count?: number | null
  test_case_count?: number | null
  created_on?: string
  created_by?: number
  updated_on?: string
  updated_by?: number
}

export interface TestSuiteListResponse {
  items: TestSuite[]
  total: number
}

export interface CreateTestSuitePayload {
  site_id: number
  title: string
  description?: string
  status: TestSuiteStatus
  flow_definition: FlowDefinition
  scenario_count?: number
  test_case_count?: number
}

export interface UpdateTestSuitePayload {
  title?: string
  description?: string
  status?: TestSuiteStatus
  flow_definition?: FlowDefinition
  scenario_count?: number
  test_case_count?: number
}

// ─── Execution types ───────────────────────────────────────────────────────────

export type TestSuiteExecutionStatus =
  | 'pending'
  | 'running'
  | 'passed'
  | 'partially_passed'
  | 'failed'
  | 'error'

export interface TestSuiteExecutionSummary {
  total: number
  passed: number
  failed: number
  skipped: number
}

export interface TestSuiteExecution {
  id: number
  test_suite_id: number
  status: TestSuiteExecutionStatus
  started_at?: string | null
  ended_at?: string | null
  execution_summary?: TestSuiteExecutionSummary | null
  executed_by?: number | null
  created_on?: string
  created_by?: number
  updated_on?: string
  updated_by?: number
}

// ─── Selection tree types (used during building) ──────────────────────────────

export interface SelectionTestCase {
  id: number
  title: string
  type: string
  is_valid: boolean
}

export interface SelectionScenario {
  id: number
  title: string
  category: string
  page_id: number
  test_cases: SelectionTestCase[]
}

export interface SelectionPage {
  id: number
  page_title: string
  page_url: string
  scenarios: SelectionScenario[]
  expanded: boolean
}
