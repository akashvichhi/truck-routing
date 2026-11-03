import { useCallback } from 'react'
import dayjs from 'dayjs'

import { MAX_FORECAST_HOURS } from '@src/constants/risk_constants'

interface IForecastSliderProps {
  forecastHour: number
  departureIso: string
  onChange: (hour: number) => void
}

export function ForecastSlider({
  forecastHour,
  departureIso,
  onChange,
}: IForecastSliderProps): React.JSX.Element {
  const displayTime: string = dayjs(departureIso)
    .add(forecastHour, 'hour')
    .format('MMM D, h:mm A')

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>): void => {
      onChange(parseInt(e.target.value, 10))
    },
    [onChange],
  )

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Weather Heatmap
        </span>
        <span className="text-xs font-medium text-blue-700">
          {displayTime} (+{forecastHour}h)
        </span>
      </div>
      <input
        className="w-full accent-blue-600"
        max={MAX_FORECAST_HOURS - 1}
        min={0}
        step={1}
        type="range"
        value={forecastHour}
        onChange={handleChange}
      />
      <div className="mt-1 flex justify-between text-xs text-gray-400">
        <span>Now</span>
        <span>+48h</span>
      </div>
    </div>
  )
}
