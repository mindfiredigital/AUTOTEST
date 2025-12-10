import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from '@tanstack/react-query'
import { authApi } from '../apis/userApi'
import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'
import type { User } from '@/types'

export const useLoginMutation = () => {
  const navigate = useNavigate()
    const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authApi.login(email, password),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['get-user'] })
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
type GetMeQueryOptions = UseQueryOptions<User, unknown, User, ['get-user']>

export const useGetMeQuery = (options?: GetMeQueryOptions) => {
  return useQuery<User, unknown, User, ['get-user']>({
    queryKey: ['get-user'],
    queryFn: () => authApi.getMe(),
    retry:false,
    ...options,
  })
}
export const useLogout = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      queryClient.clear()
      navigate('/login')
      toast.success('Logged out successfully')
    },
    onError: (error: TypeError) => {
      toast.error(error?.message || 'Logout failed')
    },
  })
}
