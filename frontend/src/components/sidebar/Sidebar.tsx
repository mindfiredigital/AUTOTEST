import React from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { cn } from '@/lib/utils'
import { NavItem } from './NavItem'
import mindfireLogo from '@/assets/mindfire-logo.png'
import { useSidebar } from '@/contexts/SidebarContext'

export const Sidebar: React.FC = () => {
  const { isCollapsed, items, showBack, backTo, backLabel } = useSidebar()
  const navigate = useNavigate()

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen border-r border-border bg-background z-20 hidden lg:flex flex-col transition-all duration-300',
        isCollapsed ? 'w-20' : 'w-[260px]',
      )}
    >
      {/* Logo Section */}
      <div className="border-b border-border">
        <div className="flex items-center justify-center h-[72px]">
          {!isCollapsed ? (
            <img src={mindfireLogo} alt="Mindfire Logo" className="h-[60px]" />
          ) : (
            <img
              src="https://ourgoalplan.co.in/Images/fire-logo.png"
              alt="Mindfire Logo"
              className="h-[60px]"
            />
          )}
        </div>

        {/* Back Button */}
        {showBack && backTo && (
          <button
            type="button"
            onClick={() => navigate(backTo)}
            className="w-full flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 border-b border-border transition-colors"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-md border border-red-200 dark:border-red-800 shrink-0">
              <ArrowLeft className="h-4 w-4 text-red-500" />
            </span>
            {!isCollapsed && (backLabel || 'Back to Menu')}
          </button>
        )}
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 overflow-y-auto pt-0">
        {items.map((item) => (
          <NavItem key={item.id} item={item} isCollapsed={isCollapsed} />
        ))}
      </nav>
    </aside>
  )
}
