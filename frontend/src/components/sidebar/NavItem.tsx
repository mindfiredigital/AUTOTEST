import React from 'react'
import { Link, useParams, useMatches } from 'react-router-dom'
import { cn } from '@/lib/utils'

interface NavItemProps {
  item: {
    id: string
    label: string
    icon: React.ComponentType<React.SVGProps<SVGSVGElement>>
    path: string
  }
  isCollapsed?: boolean
  onClick?: () => void
}

export const NavItem: React.FC<NavItemProps> = ({ item, isCollapsed, onClick }) => {
  const params = useParams()
  const matches = useMatches()
  const Icon = item.icon
  // console.log("params",params)
  const actualPath = item.path.includes(':id')
    ? (() => {
        let id = params.id
        if (!id) {
          const siteInfoMatch = matches.find((m) => {
            const handle = m.handle as { sidebarId?: string } | undefined
            return handle?.sidebarId == 'site-info' && m.params.id
          })
          id = siteInfoMatch?.params.id
        }
        return item.path.replace(':id', id || '')
      })()
    : item.path
  const isActive = matches.some((match) => {
    const handle = match.handle as { sidebarId?: string } | undefined
    // console.log("handle",handle)
    return handle?.sidebarId === item.id
  })
  console.log('actualPath', actualPath)
  return (
    <Link
      to={actualPath}
      aria-label={item.label}
      aria-current={isActive ? 'page' : undefined}
      onClick={onClick}
      className={cn(
        'relative flex w-full items-center gap-4 p-3 pr-5 pl-5 text-left transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        isActive ? 'bg-accent' : 'hover:bg-accent/50',
      )}
    >
      {isActive && <div className="absolute right-0 top-0 h-full w-1.5 bg-primary" />}

      <div
        className={cn(
          'flex h-6 w-6 items-center justify-center shrink-0',
          isActive ? 'text-foreground' : 'text-muted-foreground',
        )}
      >
        <Icon className="h-5 w-5" />
      </div>

      {!isCollapsed && (
        <span
          className={cn(
            'flex-1 text-base font-medium truncate',
            isActive ? 'text-foreground' : 'text-muted-foreground',
          )}
        >
          {item.label}
        </span>
      )}
    </Link>
  )
}
