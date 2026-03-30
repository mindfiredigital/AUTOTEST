import type { FlowDefinition, TestSuite } from '@/types/testSuite'

export interface TestSuiteBuilderProps {
  siteId: number
  editSuite?: TestSuite | null
  onClose: () => void
  onSaved: () => void
  onSave: (payload: {
    title: string
    description: string
    status: string
    flow_definition: FlowDefinition
    scenario_count: number
    test_case_count: number
  }) => void
  isSaving: boolean
}

export interface PageItem {
  id: number
  page_title?: string
  page_url: string
}

export interface ScenarioItem {
  id: number
  title: string
  category: string
  page_id: number
}

export interface TestCaseItem {
  id: number
  title: string
  type: string
  is_valid: boolean
}
