import { type ReactNode } from 'react'

export type TableColumn<T> = {
  key: string
  header: ReactNode
  width?: string
  align?: 'left' | 'center' | 'right'
  render: (row: T) => ReactNode
  
}

export type TableAction<T> = {
  label: string
  destructive?: boolean
  disabled?: (row: T) => boolean
  hidden?: (row: T) => boolean
  onClick: (row: T) => void
}
