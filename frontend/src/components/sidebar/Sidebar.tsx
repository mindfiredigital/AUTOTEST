// components/sidebar/Sidebar.tsx
import React from 'react'
import { cn } from '@/lib/utils'
import { useSidebar } from '@/contexts/SidebarContext'
import mindfireLogo from '@/assets/mindfire-logo.png'
import { menuItems } from '@/constants/menuItems'
import { NavItem } from './NavItem'

export const Sidebar: React.FC = () => {
  const { isCollapsed } = useSidebar()

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen border-r border-border bg-background z-20 hidden lg:flex flex-col transition-all duration-300',
        isCollapsed ? 'w-20' : 'w-[260px]',
      )}
    >
      <div className="flex items-center justify-center h-[72px] border-b border-border">
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

      <nav className="flex-1 pt-0">
        {menuItems.map((item) => (
          <NavItem key={item.id} item={item} isCollapsed={isCollapsed} />
        ))}
      </nav>
    </aside>
  )
}
