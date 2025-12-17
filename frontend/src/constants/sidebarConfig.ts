import {
  LayoutDashboard,
  FileText,
  ListTree,
  ListChecks,
  Settings,
  CalendarClock,
} from 'lucide-react'

export type SidebarItem = {
  id: string
  label: string
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>
  path: string
}

export type SidebarConfig = {
  id: string
  pathPattern: RegExp
  items: SidebarItem[]
  showBack?: boolean
  backTo?: string
  backLabel?: string
}

export const SIDEBAR_CONFIGS: SidebarConfig[] = [
  {
    id: 'root',
    pathPattern: /^\/($|page$|user|settings)/,
    items: [
      { id: 'site', label: 'Site', icon: LayoutDashboard, path: '/' },
      { id: 'page', label: 'Page', icon: FileText, path: '/page' },
      { id: 'user', label: 'User', icon: ListTree, path: '/user' },
      { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
    ],
  },
  {
    id: 'site-info',
    pathPattern: /^\/site-info/,
    items: [
      { id: 'site-info', label: 'Site Info', icon: LayoutDashboard, path: '/site-info/:id' },
      { id: 'site-info-page', label: 'Page', icon: FileText, path: '/site-info/:id/site-page' },
      {
        id: 'test-scenario',
        label: 'Test Scenario',
        icon: ListTree,
        path: '/site-info/:id/test-scenario',
      },
      {
        id: 'test-suite',
        label: 'Test Suite',
        icon: ListChecks,
        path: '/site-info/:id/test-suite',
      },
      {
        id: 'configuration',
        label: 'Configuration',
        icon: Settings,
        path: '/site-info/:id/configuration',
      },
      {
        id: 'schedule-test',
        label: 'Schedule Test Case',
        icon: CalendarClock,
        path: '/site-info/:id/schedule',
      },
    ],
    showBack: true,
    backTo: '/',
    backLabel: 'Back to Menu',
  },
]
