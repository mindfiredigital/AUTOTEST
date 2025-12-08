import type { User } from '@/types'
import { ROLES } from '@/utils/constants'
import { hasRole } from '@/utils/helper'
import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react'

interface AuthContextType {
  user: User | null
  login: (user: User) => void
  logout: () => void
  isAuthenticated: boolean
  loading: boolean
  isAdmin: boolean | '' | undefined
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedUser = localStorage.getItem('user')

        if (storedUser && storedUser !== 'undefined') {
          const parsedUser = JSON.parse(storedUser)
          if (parsedUser && typeof parsedUser === 'object') {
            setUser(parsedUser)
          }
        }
      } catch (error) {
        console.error('Failed to parse user from localStorage:', error)
        localStorage.removeItem('user')
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()
  }, [])

  const login = useCallback((userData: User) => {
    setUser(userData)
    try {
      localStorage.setItem('user', JSON.stringify(userData))
    } catch (error) {
      console.error('Failed to save user to localStorage:', error)
    }
  }, [])

  const logout = useCallback(() => {
    setUser(null)
    try {
      localStorage.removeItem('user')
    } catch (error) {
      console.error('Failed to remove user from localStorage:', error)
    }
  }, [])

  const contextValue = useMemo(
    () => ({
      user,
      login,
      logout,
      isAuthenticated: !!user,
      loading,
      isAdmin: user?.role && hasRole(user.role, [ROLES.ADMIN]),
    }),
    [user, login, logout, loading],
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
