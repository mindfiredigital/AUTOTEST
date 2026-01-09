import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { SearchBar } from '@/components/common/SearchBar'
import { Pagination } from '@/components/common/Pagination'
import type { SortType } from '@/types'
import { AddPageSheet } from '@/components/page/AddPageDialog'
import { PageTable } from '@/components/page/PageTable'
import { useUnlinkedPagesQuery } from '@/utils/queries/pageQueries'

const Pages = () => {
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<SortType>('created_desc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [openAdd, setOpenAdd] = useState(false)

  const { data, isLoading } = useUnlinkedPagesQuery({
    page,
    limit: pageSize,
    search,
    sort,
  })

  const handleAdd = (values: { title: string; url: string }) => {
    console.log('Add page:', values)
    setOpenAdd(false)
  }

  return (
    <div className="flex h-full flex-col">
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
      >
        <Button onClick={() => setOpenAdd(true)} className="cursor-pointer">
          Add New Page
        </Button>

        <AddPageSheet open={openAdd} onOpenChange={setOpenAdd} onSubmit={handleAdd} />
      </SearchBar>

      {isLoading ? (
        <div className="flex items-center justify-center h-full">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
        </div>
      ) : (
        <>
          <PageTable data={data?.data ?? []} />

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

export default Pages
