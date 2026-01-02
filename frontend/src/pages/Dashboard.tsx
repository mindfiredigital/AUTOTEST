import * as React from 'react'
import { Button } from '@/components/ui/button'
import { SiteTable } from '@/components/site/SiteTable'
import { SearchBar } from '@/components/common/SearchBar'
import { Pagination } from '@/components/common/Pagination'
import { useSitesQuery, useCreateSiteMutation } from '@/utils/queries/sitesQuery'
import { AddSiteSheet } from '@/components/site/AddSiteDialog'
import type { SortType } from '@/types'

const Dashboard: React.FC = React.memo(() => {
  const [search, setSearch] = React.useState('')
  const [openAdd, setOpenAdd] = React.useState(false)

  const [sort, setSort] = React.useState<SortType>('created_desc')

  const [page, setPage] = React.useState(1)
  const [pageSize, setPageSize] = React.useState(10)

  const createSiteMutation = useCreateSiteMutation()

  const { data, isLoading } = useSitesQuery({
    page,
    limit: pageSize,
    search,
    sort,
  })

  const handleAdd = (values: { title: string; url: string }) => {
    createSiteMutation.mutate({
      site_title: values.title,
      site_url: values.url,
    })
    setOpenAdd(false)
  }

  return (
    <div className="flex h-full flex-col">
      <SearchBar
        searchQuery={search}
        onSearchChange={setSearch}
        sort={sort}
        onSortChange={(newSort) => {
          setSort(newSort)
          setPage(1) // reset pagination on sort change
        }}
      >
        <Button onClick={() => setOpenAdd(true)} className="cursor-pointer">
          Add New Site
        </Button>
        <AddSiteSheet open={openAdd} onOpenChange={setOpenAdd} onSubmit={handleAdd} />
      </SearchBar>

      {isLoading ? (
        <div className="flex items-center justify-center h-full">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
        </div>
      ) : (
        <>
          <SiteTable data={data?.data || []} />
          <Pagination
            currentPage={data?.meta.page ?? 1}
            totalPages={data?.meta.totalPages ?? 1}
            itemsPerPage={data?.meta.limit ?? pageSize}
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
})

Dashboard.displayName = 'Dashboard'
export default Dashboard
