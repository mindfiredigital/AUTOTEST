import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '../ui/button'
import { useNavigate } from 'react-router-dom'

const NetworkIssue = () => {
  const navigate = useNavigate()

  const handleReload = () => {
    const previousPath = sessionStorage.getItem('previous_path') || '/'
    sessionStorage.removeItem('previous_path')
    navigate(previousPath)
  }
  return (
    <div className="flex items-center justify-center  py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md -200">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">Network Issue:</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-2">
          <div className="text-[#ff0000]">No Internet Connection.</div>
          <Button onClick={handleReload}>Reload</Button>
        </CardContent>
      </Card>
    </div>
  )
}

export default NetworkIssue
