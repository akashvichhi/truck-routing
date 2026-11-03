import { useEffect, useState } from 'react'

import { fetchAddressSuggestions } from '@src/api/geocode_api'
import type { IGeocodeResult } from '@src/types/route'

const DEBOUNCE_MS = 400
const MIN_QUERY_LENGTH = 2

export function useAddressAutocomplete(query: string): {
  suggestions: IGeocodeResult[]
  isLoading: boolean
  clear: () => void
} {
  const [suggestions, setSuggestions] = useState<IGeocodeResult[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(false)

  useEffect((): (() => void) => {
    if (query.trim().length < MIN_QUERY_LENGTH) {
      setSuggestions([])
      return (): void => {}
    }

    const timer = setTimeout((): void => {
      setIsLoading(true)
      fetchAddressSuggestions(query)
        .then((results: IGeocodeResult[]): void => {
          setSuggestions(results)
        })
        .catch((): void => {
          setSuggestions([])
        })
        .finally((): void => {
          setIsLoading(false)
        })
    }, DEBOUNCE_MS)

    return (): void => clearTimeout(timer)
  }, [query])

  function clear(): void {
    setSuggestions([])
  }

  return { suggestions, isLoading, clear }
}
