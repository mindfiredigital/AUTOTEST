import { Link, useLocation } from 'react-router-dom'
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
  const { pathname } = useLocation()
  const isActive = pathname === item.path
  const Icon = item.icon

  return (
    <Link
      to={item.path}
      key={item.id}
      onClick={onClick}
      aria-label={item.label}
      aria-current={isActive ? 'page' : undefined}
      className={cn(
        'relative flex w-full items-center gap-4 px-5 py-4 text-left transition-colors',
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
        <Icon className="h-6 w-6" />
      </div>

      {!isCollapsed && (
        <span
          className={cn(
            'text-base font-medium',
            isActive ? 'text-foreground' : 'text-muted-foreground',
          )}
        >
          {item.label}
        </span>
      )}
    </Link>
  )
}
