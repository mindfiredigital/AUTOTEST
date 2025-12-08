import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '../ui/button'

interface ErrorFallbackProps {
  error: Error
}

export const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error }) => {
  const resetErrorBoundary = () => {
    window.location.reload()
  }
  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md -200">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">Something went wrong:</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-2">
          <pre className="text-[#ff0000] whitespace-pre-wrap break-words">{error.message}</pre>
          <Button onClick={resetErrorBoundary}>Try again</Button>
        </CardContent>
      </Card>
    </div>
  )
}
