import React from 'react'
import { X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useSidebar } from '@/contexts/SidebarContext'
import { useSidebarLayout } from '@/contexts/SidebarLayoutContext'
import { NavItem } from './NavItem'
import { ArrowLeft } from 'lucide-react'

export const MobileMenu: React.FC = () => {
  const { isOpen, close } = useSidebar()
  const { items, showBack, backTo, backLabel } = useSidebarLayout()
  const navigate = useNavigate()

  if (!isOpen) return null

  const handleBack = () => {
    if (backTo) navigate(backTo)
    close()
  }

  return (
    <>
      <div
        className="fixed inset-0 bg-black/50 z-40 lg:hidden"
        onClick={close}
        aria-hidden="true"
      />

      <aside className="fixed left-0 top-0 h-screen w-[260px] border-r border-border bg-background z-50 lg:hidden transition-transform">
        <div className="flex h-full flex-col">
          <div className="h-[72px] border-b border-border flex items-center justify-between px-4">
            {showBack && backTo && (
              <button
                type="button"
                onClick={handleBack}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-500 hover:bg-red-50"
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-md border">
                  <ArrowLeft className="text-red-500 text-lg leading-none" />
                </span>

                {backLabel ?? 'Back to Menu'}
              </button>
            )}

            <button onClick={close} aria-label="Close menu">
              <X className="h-6 w-6" />
            </button>
          </div>

          <nav className="flex-1 pt-0">
            {items.map((item) => (
              <NavItem key={item.id} item={item} onClick={close} />
            ))}
          </nav>
        </div>
      </aside>
    </>
  )
}
