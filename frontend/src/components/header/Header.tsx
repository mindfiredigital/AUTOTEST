import { Menu } from 'lucide-react'
import { useMatches } from 'react-router-dom'
import UserMenu from './UserMenu'
import { useSidebar } from '@/contexts/SidebarContext'
import type { RouteHandle } from '@/types'
export const Header = () => {
  const { toggleCollapse, toggle } = useSidebar()
  const matches = useMatches()

  const handleToggle = () => {
    if (window.innerWidth >= 1024) {
      toggleCollapse()
    } else {
      toggle()
    }
  }

  const currentRoute = matches
    .slice()
    .reverse()
    .find(
      (match): match is typeof match & { handle: RouteHandle } =>
        typeof match.handle === 'object' && match.handle !== null && 'title' in match.handle,
    )

  const title = currentRoute?.handle.title ?? 'Site'

  return (
    <header className="sticky top-0 z-10 h-[72px] border-b border-border bg-background">
      <div className="flex h-full items-center justify-between px-5">
        <div className="flex h-full items-center gap-4">
          <button
            className="p-2 border border-border rounded-md bg-gray-100 cursor-pointer"
            onClick={handleToggle}
            aria-label="Toggle menu"
          >
            <Menu className="h-6 w-6" />
          </button>

          <h1 className="text-xl font-semibold text-foreground">{title}</h1>
        </div>

        <UserMenu />
      </div>
    </header>
  )
}
