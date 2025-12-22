import type { User } from '@/types'
import api from '../axios'

export const authApi = {
  login: async (email: string, password: string): Promise<User> => {
    console.log('email: string, password: string', email, password)
    const { data } = await api.post('/auth/login', { email, password })
    return data
  },

  register: async (
    email: string,
    password: string,
    firstname: string,
    lastname: string,
    username: string,
  ): Promise<User> => {
    const { data } = await api.post('/auth/register', {
      email,
      password,
      firstname,
      lastname,
      username,
    })
    return data
  },
  getMe: async (): Promise<User> => {
    const { data } = await api.get('/auth/me')
    return data
  },
  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
    localStorage.clear()
  },
}
