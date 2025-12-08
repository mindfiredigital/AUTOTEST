import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'

const NotFound: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-center px-6">
      <h1 className="text-6xl font-bold text-blue-600 mb-4">404</h1>
      <h2 className="text-2xl font-semibold mb-2">Page Not Found</h2>
      <p className="text-gray-600 dark:text-gray-400 mb-6">
        Oops! The page you are looking for doesn’t exist or has been moved.
      </p>

      <div className="flex gap-4">
        <Button onClick={() => navigate('/')}>Go Home</Button>
        <Button variant="outline" onClick={() => navigate('/login')}>
          Login
        </Button>
      </div>
    </div>
  )
}

export default NotFound
