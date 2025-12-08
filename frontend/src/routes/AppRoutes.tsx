import React, { lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import InlineLoader from '@/components/layout/InlineLoader'

const Layout = lazy(() => import('@/components/layout/Layout'))
const ProtectedRoute = lazy(() => import('../routes/ProtectedRoute'))
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const LoginForm = lazy(() => import('@/components/auth/LoginForm'))
const RegisterForm = lazy(() => import('@/components/auth/RegisterForm'))
const NetworkIssue = lazy(() => import('@/components/layout/NetworkIssue'))
const NotFound = lazy(() => import('@/components/layout/NotFound'))

export const AppRoutes: React.FC = React.memo(() => {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return <InlineLoader />
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginForm />}
      />
      <Route
        path="/register"
        element={isAuthenticated ? <Navigate to="/" replace /> : <RegisterForm />}
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="network-issue" element={<NetworkIssue />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
})

AppRoutes.displayName = 'AppRoutes'
