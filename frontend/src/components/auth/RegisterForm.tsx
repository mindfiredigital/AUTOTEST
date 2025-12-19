import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { toast } from 'sonner'
import { Loader2 } from 'lucide-react'
import { useRegisterMutation } from '@/utils/queries/authQueries'
import { useForm } from 'react-hook-form'
import mindfireLogo from '@/assets/mindfire-logo.png'

type RegisterValues = {
  firstname: string
  lastname: string
  email: string
  password: string
  username: string
}

const RegisterForm: React.FC = () => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<RegisterValues>({
    defaultValues: { firstname: '', lastname: '', email: '', password: '', username: '' },
  })

  const registerMutation = useRegisterMutation()

  const onSubmit = (data: RegisterValues) => {
    registerMutation.mutate(data, {
      onSuccess: () => {
        toast.success('Account created successfully!')
        reset()
      },
      onError: (error: unknown) => {
        const err = error as { response?: { data?: { detail?: string } } }
        toast.error(err?.response?.data?.detail || 'Registration failed')
      },
    })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="flex flex-col items-center w-full">
        <img src={mindfireLogo} alt="Mindfire Logo" className="h-14 mt-4 mb-6" />

        <Card className="w-full max-w-md shadow-lg rounded-xl border">
          <CardHeader className="text-center pb-2">
            <h2 className="text-xl font-semibold">Sign up to your account</h2>
          </CardHeader>

          <CardContent className="space-y-5">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="firstname">First Name</Label>
                <Input
                  id="firstname"
                  placeholder="Enter first name"
                  {...register('firstname', {
                    required: 'First name is required',
                    maxLength: { value: 50, message: 'First name must be max 50 characters' },
                  })}
                  disabled={registerMutation.isPending}
                  className="h-11"
                />
                {errors.firstname && (
                  <p className="text-xs text-red-500">{errors.firstname.message}</p>
                )}
              </div>

              <div className="space-y-1">
                <Label htmlFor="lastname">Last Name</Label>
                <Input
                  id="lastname"
                  placeholder="Enter last name"
                  {...register('lastname', {
                    required: 'Last name is required',
                    maxLength: { value: 50, message: 'last name must be max 50 characters' },
                  })}
                  disabled={registerMutation.isPending}
                  className="h-11"
                />
                {errors.lastname && (
                  <p className="text-xs text-red-500">{errors.lastname.message}</p>
                )}
              </div>
              <div className="space-y-1">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="Enter username here"
                  {...register('username', {
                    required: 'Username is required',
                    maxLength: { value: 50, message: 'username must be max 50 characters' },
                  })}
                  disabled={registerMutation.isPending}
                  className="h-11"
                />
                {errors.username && (
                  <p className="text-xs text-red-500">{errors.username.message}</p>
                )}
              </div>
              <div className="space-y-1">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter email address"
                  {...register('email', {
                    required: 'Email is required',
                    pattern: { value: /^\S+@\S+$/i, message: 'Invalid email address' },
                    maxLength: { value: 50, message: 'email must be max 50 characters' },
                  })}
                  disabled={registerMutation.isPending}
                  className="h-11"
                />
                {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
              </div>

              <div className="space-y-1">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter password"
                  {...register('password', {
                    required: 'Password is required',
                    minLength: { value: 6, message: 'Password must be at least 6 characters' },
                    maxLength: { value: 50, message: 'Password must be max 50 characters' },
                  })}
                  disabled={registerMutation.isPending}
                  className="h-11"
                />
                {errors.password && (
                  <p className="text-xs text-red-500">{errors.password.message}</p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full bg-red-600 hover:bg-red-700 h-11 text-white"
                disabled={registerMutation.isPending}
              >
                {registerMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Sign Up
              </Button>
            </form>

            <div className="text-center text-sm text-gray-600 pt-2">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-red-600 hover:underline">
                Sign In
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default RegisterForm
