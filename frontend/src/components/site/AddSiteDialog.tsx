import { useForm } from 'react-hook-form'
import { X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetFooter } from '@/components/ui/sheet'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type FormValues = {
  title: string
  url: string
}

type Props = {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (values: FormValues) => void
}

export function AddSiteSheet({ open, onOpenChange, onSubmit }: Props) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>()

  const submitHandler = (values: FormValues) => {
    onSubmit(values)
    reset()
    onOpenChange(false)
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex h-full w-[420px] flex-col p-0">
        {/* HEADER */}
        <SheetHeader className="relative border-b px-6 py-4">
          <SheetTitle>Add New Site</SheetTitle>

          <button
            onClick={() => onOpenChange(false)}
            className="absolute right-4 top-4 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </SheetHeader>

        {/* ✅ FORM WRAPS BODY + FOOTER */}
        <form onSubmit={handleSubmit(submitHandler)} className="flex h-full flex-col">
          {/* BODY */}
          <div className="flex-1 space-y-6 px-6 py-6">
            <div className="space-y-2">
              <Label>Site Title</Label>
              <Input
                placeholder="Enter site title"
                {...register('title', { required: 'Title is required' })}
              />
              {errors.title && <p className="text-xs text-destructive">{errors.title.message}</p>}
            </div>

            <div className="space-y-2">
              <Label>Site URL</Label>
              <Input
                placeholder="Enter site URL"
                {...register('url', {
                  required: 'URL is required',
                  pattern: {
                    value: /^https?:\/\/.+$/,
                    message: 'Enter a valid URL',
                  },
                })}
              />
              {errors.url && <p className="text-xs text-destructive">{errors.url.message}</p>}
            </div>
          </div>

          {/* FOOTER */}
          <SheetFooter className="border-t px-6 py-4">
            <div className="flex w-full justify-end gap-3">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" className="bg-red-600 hover:bg-red-700">
                Add
              </Button>
            </div>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  )
}
