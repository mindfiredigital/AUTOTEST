import { RouterProvider } from 'react-router-dom'
import { ErrorBoundary } from 'react-error-boundary'
import { Toaster } from '@/components/ui/sonner'
import { ErrorFallback } from '@/components/layout/ErrorFallBack'
import { memo, Suspense } from 'react'
import InlineLoader from './components/layout/InlineLoader'
import { router } from './routes/router'

const App = memo(() => {
  return (
    <Suspense fallback={<InlineLoader />}>
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <RouterProvider router={router} />
      </ErrorBoundary>
      <Toaster richColors position="bottom-right" />
    </Suspense>
  )
})

App.displayName = 'App'
export default App
