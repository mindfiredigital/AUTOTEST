import React, { useState } from 'react'
import { Link, useLocation, matchPath } from 'react-router-dom'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavChild {
  id: string
  label: string
  path: string
  children?: NavChild[]
}

interface NavItemProps {
  item: {
    id: string
    label: string
    icon: React.ComponentType<React.SVGProps<SVGSVGElement>>
    path: string
    children?: NavChild[]
  }
  isCollapsed?: boolean
  onClick?: () => void
  level?: number
}

export const NavItem: React.FC<NavItemProps> = ({ item, isCollapsed, onClick, level = 0 }) => {
  const { pathname } = useLocation()
  const Icon = item.icon
  const hasChildren = !!item.children?.length
  const [open, setOpen] = useState(false)
  const isActive = !!matchPath({ path: item.path, end: false }, pathname)
  const paddingLeft = isCollapsed ? 'pl-7' : `pl-${level === 0 ? 5 : 8}`

  const handleParentClick = (e: React.MouseEvent) => {
    if (hasChildren) {
      e.preventDefault()
      setOpen((prev) => !prev)
    } else if (onClick) {
      onClick()
    }
  }

  return (
    <div className="relative">
      <Link
        to={
          item.path.includes(':id')
            ? item.path.replace(':id', pathname.split('/')[2] || '')
            : item.path
        }
        aria-label={item.label}
        aria-current={isActive ? 'page' : undefined}
        onClick={handleParentClick}
        className={cn(
          'relative flex w-full items-center gap-4 p-3 pr-5 text-left transition-colors',
          paddingLeft,
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          isActive ? 'bg-accent' : 'hover:bg-accent/50',
        )}
      >
        {isActive && <div className="absolute right-0 top-0 h-full w-1.5 bg-primary" />}

        <div
          className={cn(
            'flex h-6 w-6 items-center justify-center',
            isActive ? 'text-foreground' : 'text-muted-foreground',
          )}
        >
          <Icon className="h-5 w-5" />
        </div>

        {!isCollapsed && (
          <span
            className={cn(
              'flex-1 text-base font-medium',
              isActive ? 'text-foreground' : 'text-muted-foreground',
            )}
          >
            {item.label}
          </span>
        )}

        {hasChildren && !isCollapsed && (
          <button
            type="button"
            onClick={handleParentClick}
            className="ml-auto flex items-center text-muted-foreground"
            aria-label={open ? 'Collapse submenu' : 'Expand submenu'}
          >
            {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        )}
      </Link>

      {/* Submenu (optional) */}
      {hasChildren && open && (
        <div className="mt-1 space-y-1">
          {item.children!.map((child) => (
            <NavItem
              key={child.id}
              item={{ ...child, icon: item.icon }}
              isCollapsed={isCollapsed}
              onClick={onClick}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
