import { useState, useCallback } from 'react'

import { ForecastSlider } from '@src/pages/home/components/forecast_slider'
import { RouteMap } from '@src/pages/home/components/route_map'
import { RoutePanel } from '@src/pages/home/components/route_panel'
import { TripForm } from '@src/pages/home/components/trip_form'
import { useTripForm } from '@src/pages/home/hooks/use_trip_form'
import { useRoutesMutation } from '@src/queries/route_queries'
import { ErrorState } from '@src/ui/feedback/error_state'
import { LoadingSpinner } from '@src/ui/feedback/loading_spinner'
import type { IRoutesResponse } from '@src/types/route'
import { useForecastSlider } from '@src/hooks/use_forecast_slider'

export default function HomePage(): React.JSX.Element {
  const { values, errors, setField, buildRequest } = useTripForm()
  const { forecastHour, setForecastHour, reset: resetSlider } = useForecastSlider()
  const [selectedRouteIndex, setSelectedRouteIndex] = useState<number>(0)
  const [result, setResult] = useState<IRoutesResponse | null>(null)
  const [departureDatetime, setDepartureDatetime] = useState<string>('')

  const mutation = useRoutesMutation()

  const handleSubmit = useCallback((): void => {
    const req = buildRequest()
    if (!req) return

    setResult(null)
    resetSlider()
    setSelectedRouteIndex(0)
    setDepartureDatetime(req.departureDatetime)

    mutation.mutate(req, {
      onSuccess: (data: IRoutesResponse): void => {
        setResult(data)
        setSelectedRouteIndex(data.recommendedRouteIndex)
      },
    })
  }, [buildRequest, mutation, resetSlider])

  const handleSelectRoute = useCallback((index: number): void => {
    setSelectedRouteIndex(index)
  }, [])

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white px-6 py-4 shadow-sm">
        <h1 className="text-lg font-bold text-gray-900">Weather-Aware Truck Routing</h1>
        <p className="text-sm text-gray-500">Find the safest route based on weather and load</p>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="flex w-80 flex-shrink-0 flex-col gap-4 overflow-y-auto border-r border-gray-200 bg-white p-4">
          <TripForm
            errors={errors}
            isLoading={mutation.isPending}
            values={values}
            onFieldChange={setField}
            onSubmit={handleSubmit}
          />

          {mutation.isError && (
            <ErrorState
              message={mutation.error?.message ?? 'Failed to fetch routes. Please try again.'}
            />
          )}

          {result && (
            <RoutePanel
              recommendedIndex={result.recommendedRouteIndex}
              routes={result.routes}
              selectedIndex={selectedRouteIndex}
              onSelectRoute={handleSelectRoute}
            />
          )}
        </aside>

        {/* Map area */}
        <main className="relative flex flex-1 flex-col overflow-hidden">
          {mutation.isPending && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/80">
              <LoadingSpinner message="Fetching routes and weather data…" />
            </div>
          )}

          {result ? (
            <>
              <div className="flex-1 overflow-hidden">
                <RouteMap
                  departureIso={departureDatetime}
                  forecastHour={forecastHour}
                  heatmapPoints={result.heatmapPoints}
                  recommendedIndex={result.recommendedRouteIndex}
                  routes={result.routes}
                  selectedIndex={selectedRouteIndex}
                />
              </div>
              <div className="border-t border-gray-200 bg-white p-4">
                <ForecastSlider
                  departureIso={departureDatetime}
                  forecastHour={forecastHour}
                  onChange={setForecastHour}
                />
              </div>
            </>
          ) : (
            <div className="flex flex-1 items-center justify-center">
              <div className="text-center">
                <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-blue-50 flex items-center justify-center">
                  <svg className="h-8 w-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 13l4.553 2.276A1 1 0 0021 21.382V10.618a1 1 0 00-.553-.894L15 7m0 13V7m0 0L9 7" strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} />
                  </svg>
                </div>
                <p className="text-sm text-gray-400">
                  Enter your trip details and click <strong>Find Safe Routes</strong>
                </p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
