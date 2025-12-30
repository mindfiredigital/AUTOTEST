import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'
import { LogOut } from 'lucide-react'
import { useCallback } from 'react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useLogout } from '@/utils/queries/authQueries'

export default function UserMenu() {
  const { user, loading } = useAuth()

  const logoutMutation = useLogout()

  const handleLogout = useCallback(() => {
    logoutMutation.mutate()
  }, [logoutMutation])

  if (loading) {
    return <span className="text-sm text-gray-400">Loading...</span>
  }

  if (!user) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="h-10 w-10 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100 p-0 font-bold"
          aria-label="User Menu"
        >
          {user.name.charAt(0).toUpperCase()}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent className="w-56 p-2 space-y-2">
        <div className="px-2 py-1 text-sm text-gray-500 dark:text-gray-400">
          Welcome, {user.name}
        </div>
        <DropdownMenuItem onClick={handleLogout} className="flex items-center space-x-2">
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
