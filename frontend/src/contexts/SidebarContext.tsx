import React, { createContext, useContext, useState, useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { SIDEBAR_CONFIGS, type SidebarItem, type SidebarConfig } from '@/constants/sidebarConfig'

type SidebarContextType = {
  // Mobile menu state
  isOpen: boolean
  toggle: () => void
  close: () => void

  // Desktop collapse state
  isCollapsed: boolean
  toggleCollapse: () => void

  // Current sidebar configuration
  items: SidebarItem[]
  showBack: boolean
  backTo: string | null
  backLabel: string | null
  currentConfig: SidebarConfig
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined)

export const SidebarProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const { pathname } = useLocation()

  // Find matching sidebar config based on current path
  const currentConfig = useMemo(() => {
    return SIDEBAR_CONFIGS.find((config) => config.pathPattern.test(pathname)) || SIDEBAR_CONFIGS[0]
  }, [pathname])

  const value: SidebarContextType = {
    // Mobile menu controls
    isOpen,
    toggle: () => setIsOpen((prev) => !prev),
    close: () => setIsOpen(false),

    // Desktop collapse controls
    isCollapsed,
    toggleCollapse: () => setIsCollapsed((prev) => !prev),

    // Current sidebar items and configuration
    items: currentConfig.items,
    showBack: currentConfig.showBack ?? false,
    backTo: currentConfig.backTo ?? null,
    backLabel: currentConfig.backLabel ?? null,
    currentConfig,
  }

  return <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
}

/**
 * Hook to access sidebar state and configuration
 *
 * @returns {SidebarContextType} Sidebar context value
 * @throws {Error} If used outside SidebarProvider
 *
 * @example
 * ```tsx
 * const { isCollapsed, items, toggleCollapse } = useSidebar()
 * ```
 */
export const useSidebar = (): SidebarContextType => {
  const context = useContext(SidebarContext)
  if (!context) {
    throw new Error('useSidebar must be used within SidebarProvider')
  }
  return context
}
