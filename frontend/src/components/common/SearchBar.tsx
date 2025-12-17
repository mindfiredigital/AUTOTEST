import * as React from 'react'
import { Search, ArrowUpDown } from 'lucide-react'

import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'

interface SearchBarProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  children?: React.ReactNode
}

export const SearchBar: React.FC<SearchBarProps> = ({ searchQuery, onSearchChange, children }) => {
  return (
    <div className="flex items-center justify-between gap-4 pb-4">
      <div className="flex items-center gap-2">
        <div className="relative w-72">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-8"
            placeholder="Search"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>

        {/* Created select */}
        <Select>
          <SelectTrigger className="w-[120px]">
            <SelectValue placeholder="Created" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="newest">Newest</SelectItem>
            <SelectItem value="oldest">Oldest</SelectItem>
          </SelectContent>
        </Select>

        {/* A–Z toggle */}
        <Button variant="outline" className="flex items-center gap-2 font-normal">
          <ArrowUpDown className="h-4 w-4" />
          A–Z
        </Button>
      </div>

      {/* RIGHT SIDE (SLOT) */}
      <div className="flex items-center gap-2">{children}</div>
    </div>
  )
}
