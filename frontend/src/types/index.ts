export interface User {
  _id: string
  email: string
  name: string
  role: string
}

export type SortType = 'created_desc' | 'created_asc' | 'title_asc' | 'title_desc'