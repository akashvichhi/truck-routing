import { useState, useCallback } from 'react'
import dayjs from 'dayjs'

import type { IRouteRequest } from '@src/types/route'

interface IFormValues {
  origin: string
  destination: string
  departureDatetime: string
  loadWeightLbs: string
}

interface IFormErrors {
  origin?: string
  destination?: string
  departureDatetime?: string
  loadWeightLbs?: string
}

interface IUseTripForm {
  values: IFormValues
  errors: IFormErrors
  setField: (field: keyof IFormValues, value: string) => void
  buildRequest: () => IRouteRequest | null
}

function defaultDeparture(): string {
  // Default to 1 hour from now, formatted for datetime-local input
  return dayjs().add(1, 'hour').format('YYYY-MM-DDTHH:mm')
}

export function useTripForm(): IUseTripForm {
  const [values, setValues] = useState<IFormValues>({
    origin: '',
    destination: '',
    departureDatetime: defaultDeparture(),
    loadWeightLbs: '30000',
  })
  const [errors, setErrors] = useState<IFormErrors>({})

  const setField = useCallback((field: keyof IFormValues, value: string): void => {
    setValues((prev) => ({ ...prev, [field]: value }))
    setErrors((prev) => ({ ...prev, [field]: undefined }))
  }, [])

  const buildRequest = useCallback((): IRouteRequest | null => {
    const newErrors: IFormErrors = {}

    if (!values.origin.trim()) newErrors.origin = 'Origin is required'
    if (!values.destination.trim()) newErrors.destination = 'Destination is required'
    if (values.origin.trim().toLowerCase() === values.destination.trim().toLowerCase()) {
      newErrors.destination = 'Destination must differ from origin'
    }
    if (!values.departureDatetime) {
      newErrors.departureDatetime = 'Departure time is required'
    } else {
      const dt = dayjs(values.departureDatetime)
      if (!dt.isValid()) newErrors.departureDatetime = 'Invalid date/time'
      else if (dt.isBefore(dayjs().subtract(1, 'hour')))
        newErrors.departureDatetime = 'Departure cannot be in the past'
    }

    const weight = parseFloat(values.loadWeightLbs)
    if (isNaN(weight) || weight < 0) newErrors.loadWeightLbs = 'Must be a non-negative number'

    setErrors(newErrors)
    if (Object.keys(newErrors).length > 0) return null

    return {
      origin: values.origin.trim(),
      destination: values.destination.trim(),
      departureDatetime: dayjs(values.departureDatetime).toISOString(),
      loadWeightLbs: weight,
    }
  }, [values])

  return { values, errors, setField, buildRequest }
}
