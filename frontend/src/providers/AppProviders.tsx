import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/contexts/AuthContext'
import { SidebarLayoutProvider } from '@/contexts/SidebarLayoutContext'
// import { ThemeProvider } from '@/components/ui/theme-provider'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export const AppProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      {/* <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme"> */}
      <SidebarLayoutProvider>
        <AuthProvider>{children}</AuthProvider>
        {/* </ThemeProvider> */}
      </SidebarLayoutProvider>
    </QueryClientProvider>
  )
}
