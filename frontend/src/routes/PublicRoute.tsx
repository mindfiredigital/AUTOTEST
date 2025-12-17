import React, { type ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import InlineLoader from '@/components/layout/InlineLoader'

type Props = {
  children: ReactNode
}

const PublicRoute: React.FC<Props> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth()

  if (loading) return <InlineLoader />

  if (isAuthenticated) return <Navigate to="/" replace />

  return <>{children}</>
}

export default PublicRoute
