import { useState, useCallback } from 'react'

import { MAX_FORECAST_HOURS } from '@src/constants/risk_constants'

interface IUseForecastSlider {
  forecastHour: number
  setForecastHour: (hour: number) => void
  reset: () => void
}

export function useForecastSlider(): IUseForecastSlider {
  const [forecastHour, setForecastHourState] = useState<number>(0)

  const setForecastHour = useCallback((hour: number): void => {
    setForecastHourState(Math.max(0, Math.min(hour, MAX_FORECAST_HOURS - 1)))
  }, [])

  const reset = useCallback((): void => {
    setForecastHourState(0)
  }, [])

  return { forecastHour, setForecastHour, reset }
}
