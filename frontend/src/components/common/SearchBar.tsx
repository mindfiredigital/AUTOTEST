import * as React from 'react'
import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import sortArrow from '@/assets/icons/sort-arrow.svg'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import type { SortType } from '@/types'
interface SearchBarProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  sort: SortType
  onSortChange: (sort: SortType) => void
  children?: React.ReactNode
}

export const SearchBar: React.FC<SearchBarProps> = ({
  searchQuery,
  onSearchChange,
  sort,
  onSortChange,
  children,
}) => {
  return (
    <div className="flex items-center justify-between gap-4 pb-4">
      <div className="flex items-center gap-2">
        {/* Search */}
        <div className="relative w-72">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-8"
            placeholder="Search"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>

        <Select
          value={sort.startsWith('created') ? sort : undefined}
          onValueChange={(value: SortType) => onSortChange(value)}
        >
          <SelectTrigger className="w-[100px] cursor-pointer">
            <SelectValue placeholder="Created" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="created_desc">Newest</SelectItem>
            <SelectItem value="created_asc">Oldest</SelectItem>
          </SelectContent>
        </Select>

        {/* A–Z toggle */}
        <Button
          variant="outline"
          className="flex items-center font-normal cursor-pointer"
          onClick={() => onSortChange(sort === 'title_asc' ? 'title_desc' : 'title_asc')}
        >
          <img src={sortArrow} alt="Sort" className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex items-center gap-2">{children}</div>
    </div>
  )
}
