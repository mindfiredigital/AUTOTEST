import { createBrowserRouter } from 'react-router-dom'
import { lazy } from 'react'
import SiteInfoPage from '@/components/site/SiteInfoPage'
import { SidebarProvider } from '@/contexts/SidebarContext'
import RootProvider from '../providers/RootProvider'
import PublicRoute from './PublicRoute'
import SiteInfoWrapper from '@/components/site/SiteInfoWrapper'
import User from '@/pages/User'
import Setting from '@/pages/Setting'
import TestScenario from '@/components/site/TestScenario'
import TestSuite from '@/components/site/TestSuite'
import Configration from '@/components/site/Configuration'
import Scheduled from '@/components/site/Schedule'
import PageInfoWrapper from '@/components/page/PageInfoWrapper'
import PageInfoPage from '@/components/page/PageInfoPage'
import SitePages from '@/components/site/SitePages'

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
            handle: {
              sidebarId: 'site',
              title: 'Sites',
            },
          },
          {
            path: 'page',
            element: <Page />,
            handle: {
              sidebarId: 'page',
              title: 'Pages',
            },
          },
          {
            path: 'user',
            element: <User />,
            handle: {
              sidebarId: 'user',
              title: 'Users',
            },
          },
          {
            path: 'settings',
            element: <Setting />,
            handle: {
              sidebarId: 'settings',
              title: 'Settings',
            },
          },
          {
            path: 'site-info/',
            element: <SiteInfoWrapper />,
            handle: {
              title: 'Site Info',
            },
            children: [
              {
                path: ':id',
                element: <SiteInfoPage />,
                handle: {
                  sidebarId: 'site-info',
                  title: 'Site Details',
                },
              },
              {
                path: ':id/site-page',
                element: <SitePages />,
                handle: {
                  sidebarId: 'site-info-page',
                  title: 'Site Pages',
                },
              },
              {
                path: ':id/test-scenario',
                element: <TestScenario />,
                handle: {
                  sidebarId: 'test-scenario',
                  title: 'Test Scenarios',
                },
              },
              {
                path: ':id/test-suite',
                element: <TestSuite />,
                handle: {
                  sidebarId: 'test-suite',
                  title: 'Test Suites',
                },
              },
              {
                path: ':id/configuration',
                element: <Configration />,
                handle: {
                  sidebarId: 'configuration',
                  title: 'Configuration',
                },
              },
              {
                path: ':id/schedule',
                element: <Scheduled />,
                handle: {
                  sidebarId: 'schedule-test',
                  title: 'Schedule',
                },
              },
            ],
          },
          {
            path: 'page-info/',
            element: <PageInfoWrapper />,
            handle: {
              sidebarId: 'page-info',
              title: 'Page Info',
            },
            children: [
              {
                path: ':id',
                element: <PageInfoPage />,
                handle: {
                  sidebarId: 'page-info',
                  title: 'Page Details',
                },
              },
              {
                path: ':id/test-scenario',
                element: <TestScenario />,
                handle: {
                  sidebarId: 'page-info',
                  title: 'Test Scenarios',
                },
              },
              {
                path: ':id/configuration',
                element: <Configration />,
                handle: {
                  sidebarId: 'page-info',
                  title: 'Configuration',
                },
              },
              {
                path: ':id/schedule',
                element: <Scheduled />,
                handle: {
                  sidebarId: 'page-info',
                  title: 'Schedule',
                },
              },
            ],
          },
        ],
      },
      { path: '*', element: <NotFound /> },
    ],
  },
])
