export interface User {
  _id: string
  email: string
  name: string
  role: string
}

export type SortType = 'created_desc' | 'created_asc' | 'title_asc' | 'title_desc'

export type PageItem = {
  id: number
  pageTitle: string
  pageUrl: string
  status: 'New' | 'Processing' | 'Done'
}

export type RouteHandle = {
  title?: string
  sidebarId?: string
}