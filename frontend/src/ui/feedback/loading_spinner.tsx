interface ILoadingSpinnerProps {
  message?: string
}

export function LoadingSpinner({ message = 'Loading…' }: ILoadingSpinnerProps): React.JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  )
}
