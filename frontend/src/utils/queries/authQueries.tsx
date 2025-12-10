import { useMutation } from '@tanstack/react-query'
import { authApi } from '../apis/userApi'
import { toast } from 'sonner'
import { useAuth } from '@/contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

export const useLoginMutation = () => {
  const { login } = useAuth()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authApi.login(email, password),
    onSuccess: (user) => {
      login(user)
      navigate('/')
    },
  })
}
export const useRegisterMutation = () => {
  const navigate = useNavigate()
  return useMutation({
    mutationFn: ({
      email,
      password,
      firstname,
      lastname,
    }: {
      email: string
      password: string
      firstname: string
      lastname: string
    }) => authApi.register(email, password, firstname, lastname),
    onSuccess: () => {
      navigate('/login')
    },
  })
}

export const useLogout = () => {
  const { logout } = useAuth()

  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      logout()
      toast.success('Logged out successfully')
    },
    onError: (error: TypeError) => {
      toast.error(error?.message || 'Logout failed')
    },
  })
}
