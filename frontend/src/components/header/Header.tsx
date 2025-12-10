import React from 'react'
import { Menu } from 'lucide-react'
import { useSidebar } from '@/contexts/SidebarContext'

export const Header: React.FC = () => {
  const { collapse, toggle } = useSidebar()

  const handleToggle = () => {
    if (window.innerWidth >= 1024) {
      collapse()
    } else {
      toggle()
    }
  }

  return (
    <header className="sticky top-0 z-10 h-[72px] border-b border-border bg-background">
      <div className="flex h-full items-center justify-between px-5">
        <div className="flex h-full items-center gap-4">
          <button
            className="p-2 bg-background border border-border rounded-md"
            onClick={handleToggle}
            aria-label="Toggle menu"
          >
            <Menu className="h-6 w-6" />
          </button>

          <h1 className="text-xl font-semibold text-foreground">Site</h1>
        </div>

        <div className="flex items-center gap-4">
          <button
            className="flex h-10 w-10 items-center justify-center rounded-full bg-muted/20 hover:bg-muted/40 transition-colors"
            aria-label="User profile"
          >
            <div className="h-9 w-9 rounded-full bg-muted" />
          </button>
        </div>
      </div>
    </header>
  )
}
