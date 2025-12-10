import type { User } from '@/types'
import api, { setAuthToken } from '../axios'

export const authApi = {
  login: async (email: string, password: string): Promise<User> => {
    console.log('email: string, password: string', email, password)
    // const { data } = await api.post('/auth/login', { email, password })
    // console.log('data', data)
    // const { accessToken, user } = data?.data
    const accessToken = '12345678'
    const user = {
      _id: '1',
      email: 'test@gmail.com',
      firstname: 'test',
      lastname: 'Doe',
      role: 'Admin',
    }
    localStorage.setItem('token', accessToken)
    setAuthToken(accessToken)

    return user
  },

  register: async (
    email: string,
    password: string,
    firstname: string,
    lastname: string,
  ): Promise<User> => {
    const { data } = await api.post('/auth/register', {
      email,
      password,
      firstname,
      lastname,
    })
    return data
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
    localStorage.removeItem('token')
    setAuthToken(null)
  },
}
