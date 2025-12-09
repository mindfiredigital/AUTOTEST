import React from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import { MoreVertical, ExternalLink } from 'lucide-react'
import { cn } from '@/lib/utils'

export type Status = 'new' | 'processing' | 'done'

export interface SiteData {
  id: string
  date: string
  title: string
  url: string
  status: Status
  selected?: boolean
}

interface StatusBadgeProps {
  status: Status
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const variants = {
    new: 'bg-[#E1EFFA] text-foreground',
    processing: 'bg-[#FFF4D3] text-foreground',
    done: 'bg-[#E2F9E1] text-foreground',
  }

  const labels = {
    new: 'New',
    processing: 'Processing',
    done: 'Done',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-md px-2.5 py-1.5 text-base font-normal border border-border',
        variants[status]
      )}
    >
      {labels[status]}
    </span>
  )
}

interface TableRowProps {
  site: SiteData
  onSelect: (id: string, selected: boolean) => void
}

const TableRow: React.FC<TableRowProps> = ({ site, onSelect }) => {
  return (
    <div
      className={cn(
        "flex h-[62px] items-center gap-4 border-b border-border px-5 transition-colors",
        site.selected && "bg-[#EDFCFF]"
      )}
    >
      <div className="flex items-center gap-4 flex-1 min-w-0">
        <div className="w-[20px]">
          <Checkbox
            checked={site.selected}
            onCheckedChange={(checked) => onSelect(site.id, checked === true)}
            aria-label={`Select ${site.title}`}
          />
        </div>
        
        <div className="flex-1 grid grid-cols-[minmax(100px,120px)_1fr_minmax(150px,200px)_minmax(80px,100px)_minmax(80px,100px)_minmax(60px,80px)] gap-2 sm:gap-4 items-center min-w-0 overflow-hidden">
          <div className="text-base font-normal text-foreground truncate" title={site.date}>
            {site.date}
          </div>
          
          <div className={cn(
            "text-base truncate",
            site.selected ? "font-semibold text-foreground" : "font-normal text-foreground"
          )} title={site.title}>
            {site.title}
          </div>
          
          <a
            href={site.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-base font-normal text-[#2761FF] hover:underline truncate flex items-center gap-1 min-w-0"
            aria-label={`Visit ${site.url}`}
            title={site.url}
          >
            <span className="truncate">{site.url}</span>
            <ExternalLink className="h-3 w-3 shrink-0" aria-hidden="true" />
          </a>
          
          <div className="flex items-center justify-center">
            <button
              className="flex h-7 w-7 items-center justify-center rounded bg-[#F1E5E5] hover:bg-[#F1E5E5]/80 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label={`Analyze ${site.title}`}
            >
              <ExternalLink className="h-3.5 w-3.5 text-foreground" aria-hidden="true" />
            </button>
          </div>
          
          <div className="flex items-center justify-center">
            <StatusBadge status={site.status} />
          </div>
          
          <div className="flex items-center justify-center">
            <button
              className="flex h-7 w-7 items-center justify-center text-foreground hover:bg-muted rounded transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label={`More options for ${site.title}`}
            >
              <MoreVertical className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

interface TableHeaderProps {
  onSelectAll: (selected: boolean) => void
  allSelected: boolean
}

const TableHeader: React.FC<TableHeaderProps> = ({ onSelectAll, allSelected }) => {
  return (
    <div className="sticky top-[148px] z-10 h-[57px] bg-[#F6F3F3] border-b border-border">
      <div className="flex h-full items-center gap-4 px-5">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <div className="w-[20px]">
            <Checkbox
              checked={allSelected}
              onCheckedChange={(checked) => onSelectAll(checked === true)}
              aria-label="Select all sites"
            />
          </div>
          
          <div className="flex-1 grid grid-cols-[minmax(100px,120px)_1fr_minmax(150px,200px)_minmax(80px,100px)_minmax(80px,100px)_minmax(60px,80px)] gap-2 sm:gap-4 items-center min-w-0">
            <button
              className="text-base font-semibold text-foreground text-left hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              onClick={() => onSelectAll(!allSelected)}
            >
              Date
            </button>
            
            <button
              className="text-base font-semibold text-foreground text-left hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              onClick={() => onSelectAll(!allSelected)}
            >
              Title
            </button>
            
            <button
              className="text-base font-semibold text-foreground text-left hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              onClick={() => onSelectAll(!allSelected)}
            >
              URL
            </button>
            
            <div className="text-base font-semibold text-foreground text-center">
              Analyze
            </div>
            
            <button
              className="text-base font-semibold text-foreground text-center hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              onClick={() => onSelectAll(!allSelected)}
            >
              Status
            </button>
            
            <div className="text-base font-semibold text-foreground text-center">
              Action
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

interface DataTableProps {
  sites: SiteData[]
  onSitesChange: (sites: SiteData[]) => void
}

export const DataTable: React.FC<DataTableProps> = ({ sites, onSitesChange }) => {
  const allSelected = sites.length > 0 && sites.every(site => site.selected)

  const handleSelect = (id: string, selected: boolean) => {
    const updated = sites.map(site =>
      site.id === id ? { ...site, selected } : site
    )
    onSitesChange(updated)
  }

  const handleSelectAll = (selected: boolean) => {
    const updated = sites.map(site => ({ ...site, selected }))
    onSitesChange(updated)
  }

  return (
    <div className="flex flex-col">
      <TableHeader onSelectAll={handleSelectAll} allSelected={allSelected} />
      <div className="divide-y divide-border">
        {sites.map((site) => (
          <TableRow key={site.id} site={site} onSelect={handleSelect} />
        ))}
      </div>
    </div>
  )
}

