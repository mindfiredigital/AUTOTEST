import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { MoreVertical, Play } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import { useNavigate } from 'react-router-dom'
import { formatDateDDMMYYYY } from '@/utils/helper'

type Site = {
  created_on: string
  id: string
  site_title: string
  site_url: string
  status: 'New' | 'Processing' | 'Done' | 'Pause'
}

type Props = {
  data: Site[]
  onDelete: (site: Site) => void
}

export function SiteTable({ data, onDelete }: Props) {
  return (
    <div className="w-full overflow-x-auto">
      <Table className="table-fixed min-w-[700px] w-full">
        <TableHeader className="bg-muted/40">
          <TableRow>
            <TableHead className="w-[120px] min-w-[100px]">Date</TableHead>
            <TableHead className="w-[220px] min-w-[160px]">Title</TableHead>
            <TableHead className="w-[240px] min-w-[160px]">URL</TableHead>
            <TableHead className="w-[140px] min-w-[100px]">Status</TableHead>
            <TableHead className="w-[120px] min-w-[90px] text-center">Analyze</TableHead>
            <TableHead className="w-[80px] min-w-[60px] text-right">Action</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {data.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                No sites available
              </TableCell>
            </TableRow>
          ) : (
            data.map((site) => (
              <TableRow key={site.id} className="border-b last:border-b-0 hover:bg-gray-50">
                {/* Date */}
                <TableCell className="text-muted-foreground">
                  {formatDateDDMMYYYY(site.created_on)}
                </TableCell>

                {/* Title */}
                <TableCell className="w-[220px]">
                  <div className="truncate font-medium" title={site.site_title}>
                    {site.site_title}
                  </div>
                </TableCell>

                {/* URL */}
                <TableCell className="w-[240px]">
                  <div className="w-full overflow-hidden">
                    <a
                      href={site.site_url}
                      target="_blank"
                      rel="noreferrer"
                      className="block truncate text-primary hover:underline"
                      title={site.site_url}
                      onClick={(e) => e.stopPropagation()}
                    >
                      {site.site_url}
                    </a>
                  </div>
                </TableCell>

                {/* Status */}
                <TableCell className="w-[140px]">
                  <StatusPill status={site.status} />
                </TableCell>

                {/* Analyze */}
                <TableCell className="w-[120px] text-center">
                  <AnalyzeButton status={site.status} />
                </TableCell>

                {/* Actions */}
                <TableCell className="w-[80px] text-right">
                  <RowActions site={site} onDelete={onDelete} />
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}



function StatusPill({ status }: { status: Site['status'] }) {
  const styles = {
    New: 'bg-blue-100 text-blue-700',
    Processing: 'bg-amber-100 text-amber-700',
    Done: 'bg-emerald-100 text-emerald-700',
    Pause: 'bg-gray-100 text-gray-700',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-medium',
        styles[status],
      )}
    >
      {status}
    </span>
  )
}


function AnalyzeButton({ status }: { status: Site['status'] }) {
  if (status === 'Processing') {
    return (
      <div className="mx-auto h-5 w-5 animate-spin rounded-full border-2 border-muted border-t-primary" />
    )
  }

  return (
    <Button size="icon" variant="ghost" className="h-8 w-8 cursor-pointer">
      <Play className="h-4 w-4 text-muted-foreground" />
    </Button>
  )
}



function RowActions({ site, onDelete }: { site: Site; onDelete: (site: Site) => void }) {
  const navigate = useNavigate()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button size="icon" variant="ghost" className="h-8 w-8 cursor-pointer">
          <MoreVertical className="h-4 w-4 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-44">
        <DropdownMenuItem
          onClick={() => navigate(`/site-info/${site.id}`)}
          className="cursor-pointer"
        >
          Navigate to Site
        </DropdownMenuItem>

        <DropdownMenuItem
          className="cursor-pointer text-destructive"
          onClick={() => onDelete(site)}
        >
          Delete Site
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
