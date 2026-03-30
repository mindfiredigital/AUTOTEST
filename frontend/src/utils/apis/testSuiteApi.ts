import api from '../axios'
import type {
  TestSuite,
  TestSuiteListResponse,
  TestSuiteExecution,
  CreateTestSuitePayload,
  UpdateTestSuitePayload,
} from '@/types/testSuite'

export const testSuiteApi = {
  listTestSuites: async (siteId: number, page = 1, limit = 20): Promise<TestSuiteListResponse> => {
    const { data } = await api.get('/test-suites', { params: { site_id: siteId, page, limit } })
    return data
  },

  createTestSuite: async (payload: CreateTestSuitePayload): Promise<TestSuite> => {
    const { data } = await api.post('/test-suites', payload)
    return data
  },

  getTestSuite: async (suiteId: number): Promise<TestSuite> => {
    const { data } = await api.get(`/test-suites/${suiteId}`)
    return data
  },

  updateTestSuite: async (suiteId: number, payload: UpdateTestSuitePayload): Promise<TestSuite> => {
    const { data } = await api.put(`/test-suites/${suiteId}`, payload)
    return data
  },

  deleteTestSuite: async (suiteId: number): Promise<void> => {
    await api.delete(`/test-suites/${suiteId}`)
  },

  executeTestSuite: async (suiteId: number): Promise<TestSuiteExecution> => {
    const { data } = await api.post(`/test-suites/${suiteId}/execute`)
    return data
  },
}
