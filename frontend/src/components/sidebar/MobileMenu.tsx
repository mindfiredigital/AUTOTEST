// components/sidebar/MobileMenu.tsx
import React from 'react'
import { X } from 'lucide-react'
import { useSidebar } from '@/contexts/SidebarContext'
import { menuItems } from '@/constants/menuItems'
import { NavItem } from './NavItem'

export const MobileMenu: React.FC = () => {
  const { isOpen, close } = useSidebar()

  if (!isOpen) return null

  return (
    <>
      <div
        className="fixed inset-0 bg-black/50 z-40 lg:hidden"
        onClick={close}
        aria-hidden="true"
      />

      <aside className="fixed left-0 top-0 h-screen w-[260px] border-r border-border bg-background z-50 lg:hidden transition-transform">
        <div className="flex h-full flex-col">
          <div className="h-[72px] border-b border-border flex items-center justify-end px-4">
            <button onClick={close} aria-label="Close menu">
              <X className="h-6 w-6" />
            </button>
          </div>

          <nav className="flex-1 pt-0">
            {menuItems.map((item) => (
              <NavItem key={item.id} item={item} onClick={close} />
            ))}
          </nav>
        </div>
      </aside>
    </>
  )
}
