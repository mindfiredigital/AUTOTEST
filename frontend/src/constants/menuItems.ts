import { LayoutDashboard, File, User, Settings } from 'lucide-react'

export const menuItems = [
  { id: 'site', label: 'Site', icon: LayoutDashboard, path: '/' },
  { id: 'page', label: 'Page', icon: File, path: '/page' },
  { id: 'user', label: 'User', icon: User, path: '/user' },
  { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
]
