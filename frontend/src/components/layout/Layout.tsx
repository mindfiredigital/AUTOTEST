import React, { memo } from 'react'
import { Outlet } from 'react-router-dom'
import { Header } from '../header/Header'
import { Sidebar } from '../sidebar/Sidebar'
import { MobileMenu } from '../sidebar/MobileMenu'
import { cn } from '@/lib/utils'
import { useSidebar } from '@/contexts/SidebarContext'

const Layout: React.FC = memo(() => {
  const { isCollapsed } = useSidebar()

  return (
    <div className="flex min-h-screen bg-background">
      <MobileMenu />
      <Sidebar />
      <main
        className={cn(
          'flex flex-col flex-1 min-h-screen transition-all duration-300',
          'lg:ml-20',
          !isCollapsed && 'lg:ml-[260px]',
        )}
        role="main"
        id="main-content"
        tabIndex={-1}
      >
        <Header />
        <div className="m-5">
          <Outlet />
        </div>
      </main>
    </div>
  )
})

Layout.displayName = 'Layout'
export default Layout
