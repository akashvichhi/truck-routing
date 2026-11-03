interface IErrorStateProps {
  message: string
}

export function ErrorState({ message }: IErrorStateProps): React.JSX.Element {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4">
      <p className="text-sm font-medium text-red-700 w-full break-words">{message}</p>
    </div>
  )
}
