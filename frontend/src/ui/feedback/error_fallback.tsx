interface IErrorFallbackProps {
  title?: string
  message?: string
  onReset?: () => void
}

export function ErrorFallback({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  onReset,
}: IErrorFallbackProps): React.JSX.Element {
  return (
    <div className="flex min-h-[200px] flex-col items-center justify-center gap-4 p-8">
      <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
      <p className="text-sm text-gray-500">{message}</p>
      {onReset ? (
        <button
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          onClick={onReset}
          type="button"
        >
          Try again
        </button>
      ) : (
        <button
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          onClick={(): void => window.location.reload()}
          type="button"
        >
          Reload page
        </button>
      )}
    </div>
  )
}
