import { useQuery } from '@tanstack/react-query'
import { pageApi } from '../apis/pageApi'
import type { SortType } from '@/types'

export const useUnlinkedPagesQuery = ({
  page,
  limit,
  search,
  sort,
}: {
  page: number
  limit: number
  search?: string
  sort?: SortType
}) => {
  return useQuery({
    queryKey: ['unlinked-pages', page, limit, search, sort],
    queryFn: () =>
      pageApi.getUnlinkedPages({
        page,
        limit,
        search,
        sort,
      }),
  })
}
