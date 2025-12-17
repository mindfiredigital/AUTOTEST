import React from 'react'
import { Outlet, useParams } from 'react-router-dom'
import NotFound from '@/components/layout/NotFound'

const SiteInfoWrapper: React.FC = () => {
  const { id } = useParams()

  if (!id) return <NotFound />

  return <Outlet />
}

export default SiteInfoWrapper
