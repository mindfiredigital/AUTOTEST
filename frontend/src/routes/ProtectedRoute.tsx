import React, { memo } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import InlineLoader from '@/components/layout/InlineLoader'

interface ProtectedRouteProps {
  children: React.ReactNode
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = memo(({ children }) => {
  const { loading, status } = useAuth()

  if (loading || status === 'unknown') {
    return <InlineLoader />
  }

  if (status === 'unauthenticated') {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
})

ProtectedRoute.displayName = 'ProtectedRoute'
export default ProtectedRoute
