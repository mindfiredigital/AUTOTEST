import type { User } from '@/types'
import { ROLES } from '@/utils/constants'
import { hasRole } from '@/utils/helper'
import { useGetMeQuery } from '@/utils/queries/authQueries'
import React, { createContext, useContext, useMemo } from 'react'
import { useLocation } from 'react-router-dom'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  isAdmin: boolean | '' | undefined
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation()
  const isAuthPage = ['/register'].includes(location.pathname)

  const { data, isLoading } = useGetMeQuery({
    enabled: !isAuthPage,
    queryKey: ['get-user'],
  })

  const contextValue = useMemo(
    () => ({
      user: data ? data : null,
      isAuthenticated: !!data,
      loading: isLoading,
      isAdmin: data?.role && hasRole(data.role, [ROLES.ADMIN]),
    }),
    [data, isLoading],
  )

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
