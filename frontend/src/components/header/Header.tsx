import React from 'react'
import { Menu } from 'lucide-react'
import UserMenu from './UserMenu'
import { useSidebar } from '@/contexts/SidebarContext'

export const Header: React.FC = () => {
  const { toggleCollapse, toggle } = useSidebar()

  const handleToggle = () => {
    if (window.innerWidth >= 1024) {
      toggleCollapse()
    } else {
      toggle()
    }
  }

  return (
    <header className="sticky top-0 z-10 h-[72px] border-b border-border bg-background">
      <div className="flex h-full items-center justify-between px-5">
        <div className="flex h-full items-center gap-4">
          <button
            className="p-2  border border-border rounded-md  bg-gray-100 cursor-pointer"
            onClick={handleToggle}
            aria-label="Toggle menu"
          >
            <Menu className="h-6 w-6 cursor-pointer" />
          </button>

          <h1 className="text-xl font-semibold text-foreground">Site</h1>
        </div>

        <div className="flex items-center gap-4">
          <UserMenu />
        </div>
      </div>
    </header>
  )
}
