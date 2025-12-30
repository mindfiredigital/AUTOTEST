import React, { memo } from 'react'

const InlineLoader: React.FC = memo(() => (
  <div className="flex h-screen items-center justify-center">
    <div
      className="h-8 w-8 animate-spin rounded-full border-b-2 border-blue-600"
      role="status"
      aria-label="Loading"
    />
  </div>
))

InlineLoader.displayName = 'InlineLoader'
export default InlineLoader
