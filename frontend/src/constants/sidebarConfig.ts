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

export type SidebarDefinition = {
  id: string
  match: (pathname: string) => boolean
  items: SidebarItem[]
  showBack?: boolean
  backTo?: string
  backLabel?: string
}

export const SIDEBARS: SidebarDefinition[] = [
  {
    id: 'root',
    match: (p) => p === '/' || p.startsWith('/user') || p.startsWith('/settings'),
    items: [
      { id: 'site', label: 'Site', icon: LayoutDashboard, path: '/' },
      { id: 'page', label: 'Page', icon: FileText, path: '/page' },
      { id: 'user', label: 'User', icon: ListTree, path: '/user' },
      { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
    ],
  },
  {
    id: 'site-info',
    match: (p) => p.startsWith('/site-info'),
    items: [
      { id: 'site-info', label: 'Site Info', icon: LayoutDashboard, path: '/site-info/:id' },
      { id: 'page', label: 'Page', icon: FileText, path: '/site-info/page' },
      {
        id: 'test-scenario',
        label: 'Test Scenario',
        icon: ListTree,
        path: '/site-info/test-scenario',
      },
      { id: 'test-suite', label: 'Test Suite', icon: ListChecks, path: '/site-info/test-suite' },
      {
        id: 'configuration',
        label: 'Configuration',
        icon: Settings,
        path: '/site-info/configuration',
      },
      {
        id: 'schedule-test',
        label: 'Schedule Test Case',
        icon: CalendarClock,
        path: '/site-info/schedule',
      },
    ],
    showBack: true,
    backTo: '/',
    backLabel: 'Back to Menu',
  },
]
