import React from 'react'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useSidebar } from '@/contexts/SidebarContext'
import { useSidebarLayout } from '@/contexts/SidebarLayoutContext'
import mindfireLogo from '@/assets/mindfire-logo.png'
import { NavItem } from './NavItem'
import { ArrowLeft } from 'lucide-react'

export const Sidebar: React.FC = () => {
  const { isCollapsed } = useSidebar()
  const { items, showBack, backTo, backLabel } = useSidebarLayout()
  const navigate = useNavigate()

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen border-r border-border bg-background z-20 hidden lg:flex flex-col transition-all duration-300',
        isCollapsed ? 'w-20' : 'w-[260px]',
      )}
    >
      <div className="border-b border-border">
        <div className="flex items-center justify-center h-[72px] ">
          {!isCollapsed ? (
            <img src={mindfireLogo} alt="Logo" className="h-[60px]" />
          ) : (
            <img
              src="https://ourgoalplan.co.in/Images/fire-logo.png"
              alt="Logo"
              className="h-[60px]"
            />
          )}
        </div>

        {showBack && backTo && (
          <button
            type="button"
            onClick={() => navigate(backTo)}
            className="w-full flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-500 hover:bg-red-50 border-b border-border"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-md border">
              <ArrowLeft className="text-red-500 text-lg leading-none" />
            </span>

            {!isCollapsed && (backLabel ?? 'Back to Menu')}
          </button>
        )}
      </div>

      <nav className="flex-1 pt-0">
        {items.map((item) => (
          <NavItem key={item.id} item={item} isCollapsed={isCollapsed} />
        ))}
      </nav>
    </aside>
  )
}
