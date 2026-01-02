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
  status: 'New' | 'Processing' | 'Done'
}

type Props = {
  data: Site[]
}

export function SiteTable({ data }: Props) {
  const navigate = useNavigate()
  console.log(data)

  return (
    <div className="">
      <Table>
        <TableHeader className="bg-muted/40">
          <TableRow>
            <TableHead className="w-[140px]">Date</TableHead>
            <TableHead>Title</TableHead>
            <TableHead className="w-60">URL</TableHead>
            <TableHead className="w-[140px]">Status</TableHead>
            <TableHead className="w-[120px] text-center">Analyze</TableHead>
            <TableHead className="w-20 text-right">Action</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {data.map((site) => (
            <TableRow
              key={site.id}
              className={'border-b last:border-b-0 hover:bg-gray-50 cursor-pointer'}
              onClick={() => navigate(`/site-info/${site.id}`)}
            >
              <TableCell className="text-muted-foreground">
                {formatDateDDMMYYYY(site.created_on)}
              </TableCell>

              <TableCell className="max-w-[260px] truncate font-medium">
                {site.site_title}
              </TableCell>

              <TableCell>
                <a
                  href={site.site_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary hover:underline"
                >
                  {site.site_url}
                </a>
              </TableCell>

              <TableCell>
                <StatusPill status={site.status} />
              </TableCell>

              <TableCell className="text-center">
                <AnalyzeButton status={site.status} />
              </TableCell>

              <TableCell className="text-right">
                <RowActions />
              </TableCell>
            </TableRow>
          ))}
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
    <Button size="icon" variant="ghost" className="h-8 w-8">
      <Play className="h-4 w-4 text-muted-foreground" />
    </Button>
  )
}

function RowActions() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button size="icon" variant="ghost" className="h-8 w-8 cursor-pointer">
          <MoreVertical className="h-4 w-4 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-44">
        <DropdownMenuItem>Edit Site Title</DropdownMenuItem>
        <DropdownMenuItem>Navigate to Site</DropdownMenuItem>
        <DropdownMenuItem>Cache mode: No-cache</DropdownMenuItem>
        <DropdownMenuItem className="text-destructive">Delete Site</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
