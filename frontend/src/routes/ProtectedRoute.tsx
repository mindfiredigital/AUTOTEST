import React, { memo } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import InlineLoader from '@/components/layout/InlineLoader'

interface ProtectedRouteProps {
  children: React.ReactNode
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = memo(({ children }) => {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return <InlineLoader />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
})

ProtectedRoute.displayName = 'ProtectedRoute'
export default ProtectedRoute
