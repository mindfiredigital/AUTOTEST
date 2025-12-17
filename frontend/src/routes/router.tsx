import { createBrowserRouter } from 'react-router-dom'
import { lazy } from 'react'
import SiteInfoPage from '@/components/site/SiteInfoPage'
import { SidebarProvider } from '@/contexts/SidebarContext'
import RootProvider from '../providers/RootProvider'
import PublicRoute from './PublicRoute'
import SiteInfoWrapper from '@/components/site/SiteInfoWrapper'

const Layout = lazy(() => import('@/components/layout/Layout'))
const ProtectedRoute = lazy(() => import('./ProtectedRoute'))
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const Page = lazy(() => import('@/pages/Page'))
const LoginForm = lazy(() => import('@/components/auth/LoginForm'))
const RegisterForm = lazy(() => import('@/components/auth/RegisterForm'))
const NetworkIssue = lazy(() => import('@/components/layout/NetworkIssue'))
const NotFound = lazy(() => import('@/components/layout/NotFound'))

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootProvider />,
    children: [
      {
        path: 'login',
        element: (
          <PublicRoute>
            <LoginForm />
          </PublicRoute>
        ),
        handle: { public: true },
      },
      {
        path: 'register',
        element: (
          <PublicRoute>
            <RegisterForm />
          </PublicRoute>
        ),
        handle: { public: true },
      },
      {
        path: 'network-issue',
        element: (
          <PublicRoute>
            <NetworkIssue />
          </PublicRoute>
        ),
        handle: { public: true },
      },
      {
        path: '/',
        element: (
          <ProtectedRoute>
            <SidebarProvider>
              <Layout />
            </SidebarProvider>
          </ProtectedRoute>
        ),
        children: [
          {
            index: true,
            element: <Dashboard />,
            handle: { sidebarId: 'site' },
          },
          {
            path: 'page',
            element: <Page />,
            handle: { sidebarId: 'page' },
          },
          {
            path: 'user',
            element: <Page />,
            handle: { sidebarId: 'user' },
          },
          {
            path: 'settings',
            element: <Page />,
            handle: { sidebarId: 'settings' },
          },
          {
            path: 'site-info/',
            element: <SiteInfoWrapper />,
            children: [
              {
                path: ':id',
                element: <SiteInfoPage />,
                handle: { sidebarId: 'site-info' },
              },
              {
                path: ':id/site-page',
                element: <Page />,
                handle: { sidebarId: 'site-info-page' },
              },
              {
                path: ':id/test-scenario',
                element: <Page />,
                handle: { sidebarId: 'test-scenario' },
              },
              {
                path: ':id/test-suite',
                element: <Page />,
                handle: { sidebarId: 'test-suite' },
              },
              {
                path: ':id/configuration',
                element: <Page />,
                handle: { sidebarId: 'configuration' },
              },
              {
                path: ':id/schedule',
                element: <Page />,
                handle: { sidebarId: 'schedule-test' },
              },
            ],
          },
        ],
      },
      { path: '*', element: <NotFound /> },
    ],
  },
])
