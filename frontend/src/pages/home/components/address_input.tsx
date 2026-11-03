import React, { useCallback, useRef, useState } from 'react'
import clsx from 'clsx'

import { useAddressAutocomplete } from '@src/hooks/use_address_autocomplete'
import type { IGeocodeResult } from '@src/types/route'

interface IAddressInputProps {
  id: string
  label: string
  value: string
  placeholder?: string
  error?: string
  onChange: (value: string) => void
}

export function AddressInput({
  id,
  label,
  value,
  placeholder,
  error,
  onChange,
}: IAddressInputProps): React.JSX.Element {
  const [open, setOpen] = useState<boolean>(false)
  const { suggestions, clear } = useAddressAutocomplete(value)
  const blurTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleFocus = useCallback((): void => {
    if (blurTimer.current) clearTimeout(blurTimer.current)
    setOpen(true)
  }, [])

  const handleBlur = useCallback((): void => {
    // Delay so a click on a suggestion fires before the list disappears
    blurTimer.current = setTimeout((): void => setOpen(false), 150)
  }, [])

  const handleSelect = useCallback(
    (result: IGeocodeResult): void => {
      onChange(result.label)
      clear()
      setOpen(false)
    },
    [onChange, clear],
  )

  const showDropdown = open && suggestions.length > 0

  return (
    <div className="relative flex flex-col gap-1">
      <label className="text-sm font-medium text-gray-700" htmlFor={id}>
        {label}
      </label>
      <input
        autoComplete="off"
        className={clsx(
          'rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2',
          error
            ? 'border-red-400 focus:ring-red-300'
            : 'border-gray-300 focus:border-blue-500 focus:ring-blue-200',
        )}
        id={id}
        placeholder={placeholder}
        type="text"
        value={value}
        onBlur={handleBlur}
        onChange={(e: React.ChangeEvent<HTMLInputElement>): void => onChange(e.target.value)}
        onFocus={handleFocus}
      />
      {error && <p className="text-xs text-red-500">{error}</p>}

      {showDropdown && (
        <ul className="absolute left-0 right-0 top-full z-50 mt-1 max-h-48 overflow-y-auto rounded-md border border-gray-200 bg-white shadow-lg">
          {suggestions.map((s: IGeocodeResult, i: number) => (
            <li
              key={`${s.lat}-${s.lng}-${i}`}
              className="cursor-pointer px-3 py-2 text-sm text-gray-800 hover:bg-blue-50"
              onMouseDown={(): void => handleSelect(s)}
            >
              {s.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
