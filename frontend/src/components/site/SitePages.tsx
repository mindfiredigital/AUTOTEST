import { useState } from 'react'
import { SearchBar } from '@/components/common/SearchBar'
import { Pagination } from '@/components/common/Pagination'
import type { SortType } from '@/types'
import { SitePageTable } from './SitePageTable'
const STATIC_PAGES = [
  {
    id: '1',
    site_title: 'Home Page',
    site_url: 'https://example.com',
    status: 'Done',
    created_on: new Date().toISOString(),
  },
  {
    id: '2',
    site_title: 'About Page',
    site_url: 'https://example.com/about',
    status: 'Processing',
    created_on: new Date().toISOString(),
  },
  {
    id: '3',
    site_title: 'Contact Page',
    site_url: 'https://example.com/contact',
    status: 'New',
    created_on: new Date().toISOString(),
  },
] as const

const SitePages = () => {
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<SortType>('created_desc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  const filteredPages = STATIC_PAGES.filter(
    (p) =>
      p.site_title.toLowerCase().includes(search.toLowerCase()) ||
      p.site_url.toLowerCase().includes(search.toLowerCase()),
  )



  return (
    <div className="flex h-full flex-col">
      <SearchBar
        searchQuery={search}
        onSearchChange={setSearch}
        sort={sort}
        onSortChange={(newSort) => {
          setSort(newSort)
          setPage(1)
        }}
      ></SearchBar>

      <>
        <SitePageTable data={filteredPages as any} />

        <Pagination
          currentPage={page}
          totalPages={1}
          itemsPerPage={pageSize}
          totalItems={filteredPages.length}
          onPageChange={setPage}
          onItemsPerPageChange={(size) => {
            setPageSize(size)
            setPage(1)
          }}
        />
      </>
    </div>
  )
}

export default SitePages
