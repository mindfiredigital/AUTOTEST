import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { toast } from 'sonner'
import { Loader2 } from 'lucide-react'
import { useLoginMutation } from '@/utils/queries/authQueries'
import { useForm } from 'react-hook-form'
import mindfireLogo from '@/assets/mindfire-logo.png'

type LoginValues = {
  email: string
  password: string
}

const LoginForm: React.FC = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<LoginValues>({
    defaultValues: { email: '', password: '' },
  })

  const loginMutation = useLoginMutation()

  const onSubmit = (data: LoginValues) => {
    loginMutation.mutate(data, {
      onSuccess: () => {
        toast.success('Login successful!')
        reset()
      },
      onError: (error: unknown) => {
        const err = error as { response?: { data?: { detail?: string } } }
        toast.error(err?.response?.data?.detail || 'Login failed')
      },
    })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="flex flex-col items-center w-full">
        <img src={mindfireLogo} alt="Mindfire Logo" className="h-14 mb-6 mt-4" />

        <Card className="w-full max-w-md shadow-lg border rounded-xl">
          <CardHeader className="text-center pb-2">
            <h2 className="text-xl font-semibold">Sign in to your account</h2>
          </CardHeader>

          <CardContent className="space-y-5">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="email" className="font-medium">
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter email"
                  aria-invalid={!!errors.email}
                  {...register('email', { required: 'Email is required' })}
                  disabled={loginMutation.isPending}
                  className="h-11"
                />
                {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
              </div>

              <div className="space-y-1">
                <Label htmlFor="password" className="font-medium">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter password"
                  aria-invalid={!!errors.password}
                  {...register('password', { required: 'Password is required' })}
                  disabled={loginMutation.isPending}
                  className="h-11"
                />
                {errors.password && (
                  <p className="text-xs text-red-500">{errors.password.message}</p>
                )}
              </div>

              <div className="text-right">
                <Link to="/forgot-password" className="text-sm text-gray-600 hover:text-black">
                  Forgot Password?
                </Link>
              </div>

              <Button
                type="submit"
                className="w-full bg-red-600 hover:bg-red-700 h-11 text-white"
                disabled={loginMutation.isPending}
              >
                {loginMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Sign In
              </Button>
            </form>

            <div className="text-center text-sm text-gray-600 pt-2">
              Don’t have an account?{' '}
              <Link to="/register" className="font-semibold text-red-600 hover:underline">
                Sign up
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default LoginForm
