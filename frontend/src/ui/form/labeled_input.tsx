import clsx from 'clsx'

interface ILabeledInputProps {
  id: string
  label: string
  type?: string
  value: string
  placeholder?: string
  error?: string
  min?: string
  max?: string
  step?: string
  onChange: (value: string) => void
}

export function LabeledInput({
  id,
  label,
  type = 'text',
  value,
  placeholder,
  error,
  min,
  max,
  step,
  onChange,
}: ILabeledInputProps): React.JSX.Element {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-medium text-gray-700" htmlFor={id}>
        {label}
      </label>
      <input
        className={clsx(
          'rounded-md border px-3 py-2 text-sm shadow-sm outline-none',
          'focus:border-blue-500 focus:ring-1 focus:ring-blue-500',
          error ? 'border-red-400 bg-red-50' : 'border-gray-300 bg-white',
        )}
        id={id}
        max={max}
        min={min}
        placeholder={placeholder}
        step={step}
        type={type}
        value={value}
        onChange={(e: React.ChangeEvent<HTMLInputElement>): void => onChange(e.target.value)}
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  )
}
