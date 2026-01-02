// import sites from '@/mock/sites.json'
import api from '../axios'

export type Site = {
  created_on: string
  id: string
  site_title: string
  site_url: string
  status: 'New' | 'Processing' | 'Done'
}

export interface GetSitesParams {
  page: number
  limit: number
  search?: string
  sort?: string
}

export interface GetSitesResponse {
  data: Site[]
  meta: {
    page: number
    limit: number
    totalItems: number
    totalPages: number
  }
}

export interface CreateSitePayload {
  site_title: string
  site_url: string
}

export const siteApi = {
  getSites: async (params: GetSitesParams): Promise<GetSitesResponse> => {
    const { data } = await api.get('/sites', { params })

    return {
      data: data.data,
      meta: {
        page: data.page,
        limit: data.limit,
        totalItems: data.total,
        totalPages: Math.ceil(data.total / data.limit),
      },
    }
  },
  createSite: async (payload: CreateSitePayload) => {
    const { data } = await api.post('/sites', payload)
    return data
  },
}
