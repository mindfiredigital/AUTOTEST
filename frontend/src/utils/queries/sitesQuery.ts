import { useQuery } from '@tanstack/react-query'
import { siteApi } from '../apis/siteApi'

export const useSitesQuery = ({
  page,
  limit,
  search,
}: {
  page: number
  limit: number
  search: string
}) => {
  return useQuery({
    queryKey: ['sites', page, limit, search],
    queryFn: () =>
      siteApi.getSites({
        page,
        limit,
        search,
      }),
  })
}

export type SiteInfo = {
  id: string
  title: string
  url: string
  createdAt: string
  updatedAt: string
  stats: {
    pages: number
    testScenario: number
    testCases: number
    testSuite: number
    testEnvironment: number
    scheduleTestCase: number
  }
  analyzeStatus: 'New' | 'Processing' | 'Done'
}

export const useSiteInfoQuery = (id: string) => {
  return useQuery<SiteInfo>({
    queryKey: ['site-info', id],
    queryFn: async () => {
      // Return dummy data
      await new Promise((res) => setTimeout(res, 500)) // simulate loading
      return {
        id,
        title: 'Site User admin profile website',
        url: 'https://abc.com',
        createdAt: '2025-08-25T16:30:00Z',
        updatedAt: '2025-08-25T16:30:00Z',
        analyzeStatus: 'Processing',
        stats: {
          pages: 15,
          testScenario: 25,
          testCases: 123,
          testSuite: 78,
          testEnvironment: 56,
          scheduleTestCase: 23,
        },
      }
    },
    enabled: !!id,
  })
}
