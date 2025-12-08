import React, { memo } from 'react'
import { Outlet } from 'react-router-dom'
import Header from '../header/Header'
import BottomNav from '../header/BottomNav'

const Layout: React.FC = memo(() => {
  return (
    <main className="min-h-screen transition-colors" role="main" id="main-content" tabIndex={-1}>
      <Header />
      <div className="mx-2 my-4">
        <Outlet />
      </div>
      <BottomNav />
    </main>
  )
})

Layout.displayName = 'Layout'
export default Layout
