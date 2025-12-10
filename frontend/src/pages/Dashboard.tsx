import React, { memo } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { AdminDashboard } from '@/components/dashboard/AdminDashboard'
import { UserDashboard } from '@/components/dashboard/UserDashboard'

const Dashboard: React.FC = memo(() => {
  const { isAdmin } = useAuth()

  return <div className="w-full">{isAdmin ? <AdminDashboard /> : <UserDashboard />}</div>
})

Dashboard.displayName = 'Dashboard'

export default Dashboard
