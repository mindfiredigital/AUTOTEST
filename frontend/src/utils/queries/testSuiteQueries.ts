import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { testSuiteApi } from '../apis/testSuiteApi'
import type { CreateTestSuitePayload, UpdateTestSuitePayload } from '@/types/testSuite'

export const useTestSuitesQuery = (siteId: number | null) => {
  return useQuery({
    queryKey: ['test-suites', siteId],
    queryFn: () => testSuiteApi.listTestSuites(siteId!),
    enabled: !!siteId,
  })
}

export const useTestSuiteQuery = (suiteId: number | null) => {
  return useQuery({
    queryKey: ['test-suite', suiteId],
    queryFn: () => testSuiteApi.getTestSuite(suiteId!),
    enabled: !!suiteId,
  })
}

export const useCreateTestSuiteMutation = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateTestSuitePayload) => testSuiteApi.createTestSuite(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['test-suites', data.site_id] })
    },
  })
}

export const useUpdateTestSuiteMutation = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ suiteId, payload }: { suiteId: number; payload: UpdateTestSuitePayload }) =>
      testSuiteApi.updateTestSuite(suiteId, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['test-suites', data.site_id] })
      queryClient.invalidateQueries({ queryKey: ['test-suite', data.id] })
    },
  })
}

export const useDeleteTestSuiteMutation = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ suiteId }: { suiteId: number; siteId: number }) =>
      testSuiteApi.deleteTestSuite(suiteId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['test-suites', variables.siteId] })
    },
  })
}

export const useRunTestSuiteMutation = () => {
  return useMutation({
    mutationFn: (suiteId: number) => testSuiteApi.executeTestSuite(suiteId),
  })
}
