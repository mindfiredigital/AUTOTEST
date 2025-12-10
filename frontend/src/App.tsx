import { BrowserRouter as Router } from 'react-router-dom'
import { ErrorBoundary } from 'react-error-boundary'
import { Toaster } from '@/components/ui/sonner'
import { ErrorFallback } from '@/components/layout/ErrorFallBack'
import { AppProviders } from '@/providers/AppProviders'
import { AppRoutes } from '@/routes/AppRoutes'
import { memo, Suspense } from 'react'
import InlineLoader from './components/layout/InlineLoader'
import { SidebarProvider } from './contexts/SidebarContext'

const App = memo(() => {
  return (
    <Router>
      <AppProviders>
        <SidebarProvider>
          <Suspense fallback={<InlineLoader />}>
            <ErrorBoundary FallbackComponent={ErrorFallback}>
              <AppRoutes />
            </ErrorBoundary>
            <Toaster richColors position="bottom-right" />
          </Suspense>
        </SidebarProvider>
      </AppProviders>
    </Router>
  )
})

App.displayName = 'App'
export default App
