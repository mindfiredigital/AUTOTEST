import sites from '@/mock/sites.json'

export type Site = {
  id: string
  date: string
  title: string
  url: string
  status: 'New' | 'Processing' | 'Done'
}

export interface GetSitesParams {
  page: number
  limit: number
  search?: string
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

export const siteApi = {
  //   getSites: async (params: GetSitesParams): Promise<GetSitesResponse> => {
  //     const { data } = await api.get('/sites', { params })
  //     return data
  //   },
  //   getSitesInfo: async (params: GetSitesParams): Promise<GetSitesResponse> => {
  //     const { data } = await api.get(`/api/sites/${id}`)
  //     return data
  //   },
  getSites: async (params: GetSitesParams): Promise<GetSitesResponse> => {
    const { page, limit, search } = params

    // simulate network delay (optional)
    await new Promise((res) => setTimeout(res, 300))

    let filtered: Site[] = sites.data as Site[]

    // SEARCH (backend-like)
    if (search) {
      filtered = filtered.filter((site) => site.title.toLowerCase().includes(search.toLowerCase()))
    }

    const totalItems = filtered.length
    const totalPages = Math.ceil(totalItems / limit)

    const start = (page - 1) * limit
    const end = start + limit

    return {
      data: filtered.slice(start, end),
      meta: {
        page,
        limit,
        totalItems,
        totalPages,
      },
    }
  },
}
