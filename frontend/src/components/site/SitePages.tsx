import { useState } from 'react'
import { SearchBar } from '@/components/common/SearchBar'
import { Pagination } from '@/components/common/Pagination'
import type { SortType } from '@/types'
import { SitePageTable } from './SitePageTable'
import { useSitePagesQuery } from '@/utils/queries/sitesQuery'
import { useParams } from 'react-router-dom'

const SitePages = () => {
  const { id } = useParams<{ id: string }>()
  const siteId = Number(id)
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<SortType>('created_desc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  const { data, isLoading, isError } = useSitePagesQuery({
    siteId,
    page,
    limit: pageSize,
    search,
    sort,
  })

  return (
    <div className="flex h-full flex-col">
      {/* Search + Sort */}
      <SearchBar
        searchQuery={search}
        onSearchChange={(value) => {
          setSearch(value)
          setPage(1)
        }}
        sort={sort}
        onSortChange={(newSort) => {
          setSort(newSort)
          setPage(1)
        }}
      />

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center h-full">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
        </div>
      )}

      {isError && (
        <div className="flex flex-1 items-center justify-center text-red-500">
          Failed to load pages
        </div>
      )}

      {/* Data */}
      {!isLoading && !isError && (
        <>
          <SitePageTable data={data?.data ?? []} />

          <Pagination
            currentPage={page}
            totalPages={data?.meta.totalPages ?? 1}
            itemsPerPage={pageSize}
            totalItems={data?.meta.totalItems ?? 0}
            onPageChange={setPage}
            onItemsPerPageChange={(size) => {
              setPageSize(size)
              setPage(1)
            }}
          />
        </>
      )}
    </div>
  )
}

export default SitePages
