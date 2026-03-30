import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MoreVertical } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { TableColumn, TableAction } from './types'

type DynamicTableProps<T> = {
  data: T[]
  columns: TableColumn<T>[]
  actions?: TableAction<T>[]
  getRowKey: (row: T) => string | number
  onRowClick?: (row: T) => void
  getRowClassName?: (row: T) => string
}

export function DynamicTable<T>({
  data,
  columns,
  actions,
  getRowKey,
  onRowClick,
  getRowClassName,
}: DynamicTableProps<T>) {
  return (
    <div className="w-full overflow-x-auto">
    <Table className="table-fixed min-w-[640px] w-full">
      <TableHeader className="bg-muted/40">
        <TableRow>
          {columns.map((col) => (
            <TableHead
              key={col.key}
              className={cn(
                col.width,
                col.align === 'center' && 'text-center',
                col.align === 'right' && 'text-right',
              )}
            >
              {col.header}
            </TableHead>
          ))}
          {actions && <TableHead className="w-16 text-right">Action</TableHead>}
        </TableRow>
      </TableHeader>

      <TableBody>
        {data.length === 0 ? (
          <TableRow>
            <TableCell colSpan={columns.length + (actions ? 1 : 0)} className="text-center py-6">
              No data found
            </TableCell>
          </TableRow>
        ) : (
          data.map((row) => (
            <TableRow
              key={getRowKey(row)}
              className={cn(
                'border-b last:border-b-0',
                onRowClick && 'hover:bg-gray-50 cursor-pointer',
                getRowClassName?.(row),
              )}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((col) => {
                const value = col.render(row)

                return (
                  <TableCell
                    key={col.key}
                    className={cn(
                      col.width,
                      col.align === 'center' && 'text-center',
                      col.align === 'right' && 'text-right',
                      !col.width && 'max-w-[220px] truncate',
                    )}
                  >
                    {col.key === 'title' ? (
                      <div
                        className="truncate"
                        title={(row as any)[col.key] ?? (row as any).page_title ?? undefined}
                      >
                        {value}
                      </div>
                    ) : (
                      value
                    )}
                  </TableCell>
                )
              })}

              {actions && (
                <TableCell className="text-right">
                  <RowActions row={row} actions={actions} />
                </TableCell>
              )}
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
    </div>
  )
}

function RowActions<T>({ row, actions }: { row: T; actions: TableAction<T>[] }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button size="icon" variant="ghost" className="h-8 w-8 cursor-pointer">
          <MoreVertical className="h-4 w-4 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-44">
        {actions.map((action) => (
          <DropdownMenuItem
            key={action.label}
            disabled={action.disabled?.(row)}
            className={cn('cursor-pointer', action.destructive && 'text-destructive')}
            onClick={(e) => {
              e.stopPropagation()
              action.onClick(row)
            }}
          >
            {action.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
