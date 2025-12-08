export async function handleApi<T>(
  apiCall: () => Promise<{ data: { success: boolean; data: T } }>,
): Promise<{ success: boolean; data: T } | { success: false; message: string }> {
  try {
    const response = await apiCall()
    return { success: response.data.success, data: response.data.data }
  } catch (error: any) {
    const message = error?.response?.data?.message || 'Something went wrong'
    // console.log(error)
    return { success: false, message }
  }
}
