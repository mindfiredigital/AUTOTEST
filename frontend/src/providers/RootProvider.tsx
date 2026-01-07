import React, { Suspense } from 'react'
import { Outlet } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import InlineLoader from '@/components/layout/InlineLoader'
import { WebSocketProvider } from '@/contexts/WebSocketProvider'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

const RootProvider: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <WebSocketProvider>
          <Suspense fallback={<InlineLoader />}>
            <Outlet />
          </Suspense>
        </WebSocketProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default RootProvider
