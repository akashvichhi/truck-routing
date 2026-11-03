import React, { useEffect, useMemo, useCallback } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.heat'
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from 'react-leaflet'
import dayjs from 'dayjs'

import {
  MAP_TILE_ATTRIBUTION,
  MAP_TILE_URL,
} from '@src/constants/api_endpoints'
import {
  HEATMAP_GRADIENT,
  RISK_HEX,
  RISK_LABELS,
  ROUTE_COLORS,
} from '@src/constants/risk_constants'
import type { IHeatmapPoint, IRoute, TRiskLevel } from '@src/types/route'

interface IRouteMapProps {
  routes: IRoute[]
  selectedIndex: number
  recommendedIndex: number
  heatmapPoints: IHeatmapPoint[]
  forecastHour: number
  departureIso: string
}

// Bounds across all route geometries
function getBounds(routes: IRoute[]): L.LatLngBoundsExpression | null {
  const all: [number, number][] = routes.flatMap((r: IRoute) => r.geometry)
  if (all.length === 0) return null
  return L.latLngBounds(all as L.LatLngExpression[])
}

// Internal component that manages the heatmap layer via Leaflet directly
interface IHeatmapLayerProps {
  points: IHeatmapPoint[]
  forecastHour: number
}

function HeatmapLayer({ points, forecastHour }: IHeatmapLayerProps): null {
  const map = useMap()

  const filtered = useMemo<[number, number, number][]>(
    () =>
      points
        .filter((p: IHeatmapPoint) => p.forecastHour === forecastHour)
        .map((p: IHeatmapPoint) => [p.lat, p.lng, (p.riskValue - 1) / 4] as [number, number, number]),
    [points, forecastHour],
  )

  useEffect(() => {
    if (filtered.length === 0) return

    const heat = (L as unknown as { heatLayer: (pts: [number, number, number][], opts: object) => L.Layer }).heatLayer(
      filtered,
      {
        radius: 35,
        blur: 25,
        maxZoom: 12,
        max: 1.0,
        gradient: HEATMAP_GRADIENT,
      },
    )

    heat.addTo(map)
    return (): void => {
      map.removeLayer(heat)
    }
  }, [map, filtered])

  return null
}

// Internal component to fit map to route bounds
function BoundsFitter({ routes }: { routes: IRoute[] }): null {
  const map = useMap()

  useEffect(() => {
    const bounds = getBounds(routes)
    if (bounds) {
      map.fitBounds(bounds as L.LatLngBoundsExpression, { padding: [40, 40] })
    }
  }, [map, routes])

  return null
}

export function RouteMap({
  routes,
  selectedIndex,
  recommendedIndex: _recommendedIndex,
  heatmapPoints,
  forecastHour,
  departureIso: _departureIso,
}: IRouteMapProps): React.JSX.Element {
  const defaultCenter = useMemo<[number, number]>(() => {
    if (routes.length === 0 || routes[0].geometry.length === 0) return [39.5, -98.35]
    const mid = Math.floor(routes[0].geometry.length / 2)
    return [routes[0].geometry[mid][0], routes[0].geometry[mid][1]]
  }, [routes])

  const getRouteWeight = useCallback(
    (routeIndex: number): number => (routeIndex === selectedIndex ? 5 : 3),
    [selectedIndex],
  )

  const getRouteOpacity = useCallback(
    (routeIndex: number): number => (routeIndex === selectedIndex ? 1 : 0.55),
    [selectedIndex],
  )

  return (
    <div className="relative h-full w-full overflow-hidden rounded-xl border border-gray-200 shadow-sm">
      <MapContainer
        center={defaultCenter}
        className="h-full w-full"
        scrollWheelZoom
        zoom={5}
      >
        <TileLayer attribution={MAP_TILE_ATTRIBUTION} url={MAP_TILE_URL} />
        <BoundsFitter routes={routes} />
        <HeatmapLayer forecastHour={forecastHour} points={heatmapPoints} />

        {routes.map((route: IRoute, routeArrayIdx: number) => (
          <Polyline
            key={route.index}
            color={ROUTE_COLORS[routeArrayIdx % ROUTE_COLORS.length]}
            opacity={getRouteOpacity(route.index)}
            positions={route.geometry as L.LatLngExpression[]}
            weight={getRouteWeight(route.index)}
          />
        ))}

        {routes
          .filter((r: IRoute) => r.index === selectedIndex)
          .flatMap((r: IRoute) =>
            r.checkpoints.map((cp, i: number) => (
              <CircleMarker
                key={`${r.index}-${i}`}
                center={[cp.lat, cp.lng]}
                color={RISK_HEX[cp.riskLevel as TRiskLevel]}
                fillColor={RISK_HEX[cp.riskLevel as TRiskLevel]}
                fillOpacity={0.9}
                radius={5}
                weight={1}
              >
                <Popup>
                  <div className="min-w-[160px] text-xs">
                    <p className="mb-1 font-semibold">Mile {cp.mile}</p>
                    <p>
                      ETA:{' '}
                      <span className="font-medium">
                        {dayjs(cp.eta).format('MMM D, h:mm A')}
                      </span>
                    </p>
                    <p>Wind: {cp.windMph.toFixed(0)} mph</p>
                    <p>Rain: {cp.rainInHr.toFixed(3)} in/hr</p>
                    <p>Snow: {cp.snowInHr.toFixed(3)} in/hr</p>
                    <p className="mt-1">
                      Risk:{' '}
                      <span
                        className="font-semibold"
                        style={{ color: RISK_HEX[cp.riskLevel as TRiskLevel] }}
                      >
                        {RISK_LABELS[cp.riskLevel as TRiskLevel]}
                      </span>
                    </p>
                  </div>
                </Popup>
              </CircleMarker>
            )),
          )}
      </MapContainer>

      {/* Risk legend */}
      <div className="absolute bottom-4 right-4 z-[1000] rounded-lg bg-white/95 p-3 shadow-md">
        <p className="mb-2 text-xs font-semibold text-gray-600">Risk Level</p>
        {(['low', 'moderate', 'high', 'severe', 'no_travel'] as TRiskLevel[]).map(
          (level: TRiskLevel) => (
            <div className="mb-1 flex items-center gap-2" key={level}>
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: RISK_HEX[level] }}
              />
              <span className="text-xs text-gray-700">{RISK_LABELS[level]}</span>
            </div>
          ),
        )}
      </div>
    </div>
  )
}
