import type { User } from '@/types'
import api, { setAuthToken } from '../axios'

export const authApi = {
  login: async (email: string, password: string): Promise<User> => {
    console.log("email: string, password: string",email,password)
    // const { data } = await api.post('/auth/login', { email, password })
    // console.log('data', data)
    // const { accessToken, user } = data?.data
  const accessToken = '12345678'
    const user = {
       _id: '1',
    email: "test@gmail.com",
  firstName: 'test',
  lastName: 'Doe',
  role: "Admin",
    }
    localStorage.setItem('token', accessToken)
    setAuthToken(accessToken)

    return user
  },

  register: async (email: string, password: string, firstName: string, lastName: string): Promise<User> => {
  console.log("email: string, password: string, firstName: string, lastName: string",email, password, firstName, lastName)
    //   const { data } = await api.post('/auth/register', { email, password, firstName,
  // lastName, })
    // const { accessToken, user } = data.data
    const accessToken = '12345678'
    const user = {
       _id: '1',
    email: "test@gmail.com",
  firstName: 'test',
  lastName: 'Doe',
  role: "Admin",
    }
    
    localStorage.setItem('token', accessToken)
    setAuthToken(accessToken)

    return user
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
    localStorage.removeItem('token')
    setAuthToken(null)
  },
}

