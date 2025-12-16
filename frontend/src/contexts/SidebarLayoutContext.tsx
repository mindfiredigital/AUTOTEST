import React, { createContext, useContext, useEffect, useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { SIDEBARS, type SidebarItem } from '@/constants/sidebarConfig'

type SidebarLayoutState = {
  items: SidebarItem[]
  showBack: boolean
  backTo: string | null
  backLabel: string | null
  activeSidebarId: string
}

const SidebarLayoutContext = createContext<SidebarLayoutState | null>(null)

const STORAGE_KEY = 'app_sidebar_layout_v1'

export const SidebarLayoutProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { pathname } = useLocation()

  const definition = useMemo(() => {
    // find sidebar based on path
    const matchedSidebar = SIDEBARS.find((s) => s.match(pathname))
    if (matchedSidebar) return matchedSidebar

    // fallback to stored sidebar
    if (typeof window !== 'undefined') {
      const storedSidebarId = window.localStorage.getItem(STORAGE_KEY)
      const fromStorage = SIDEBARS.find((s) => s.id === storedSidebarId)
      if (fromStorage) return fromStorage
    }

    return SIDEBARS[0]
  }, [pathname])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, definition.id)
    }
  }, [definition.id])

  const value: SidebarLayoutState = {
    items: definition.items,
    showBack: !!definition.showBack,
    backTo: definition.backTo ?? null,
    backLabel: definition.backLabel ?? null,
    activeSidebarId: definition.id,
  }

  return <SidebarLayoutContext.Provider value={value}>{children}</SidebarLayoutContext.Provider>
}

export const useSidebarLayout = () => {
  const ctx = useContext(SidebarLayoutContext)
  if (!ctx) throw new Error('useSidebarLayout must be used within SidebarLayoutProvider')
  return ctx
}
