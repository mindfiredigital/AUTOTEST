import React from 'react'
import { Search, Calendar } from 'lucide-react'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'

interface SearchBarProps {
  searchQuery: string
  onSearchChange: (query: string) => void
}

export const SearchBar: React.FC<SearchBarProps> = ({ searchQuery, onSearchChange }) => {
  return (
    <div className="flex h-[76px] flex-col sm:flex-row items-stretch sm:items-center gap-4 border-b border-border bg-background px-4 sm:px-5">
      <div className="flex flex-1 items-center gap-0 min-w-0">
        <div className="relative flex-1 min-w-0">
          <Input
            type="search"
            placeholder="Search"
            className="pr-10"
            aria-label="Search sites"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          <Search
            className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground pointer-events-none"
            aria-hidden="true"
          />
        </div>

        <div className="flex items-center border border-l-0 border-input rounded-r-md bg-background shrink-0">
          <Select defaultValue="created">
            <SelectTrigger className="w-[140px] sm:w-[169px] border-l-0 rounded-l-none">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 shrink-0" aria-hidden="true" />
                <SelectValue placeholder="Created" />
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="created">Created</SelectItem>
              <SelectItem value="updated">Updated</SelectItem>
              <SelectItem value="name">Name</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <Button className="shrink-0 w-full sm:w-auto">Add New Site</Button>
    </div>
  )
}
