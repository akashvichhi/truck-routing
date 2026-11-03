import clsx from 'clsx'
import dayjs from 'dayjs'

import { RISK_BG_CLASSES, RISK_LABELS } from '@src/constants/risk_constants'
import type { IRoute, TRiskLevel } from '@src/types/route'

interface IRouteCardProps {
  route: IRoute
  isRecommended: boolean
  isSelected: boolean
  onSelect: () => void
}

export function RouteCard({
  route,
  isRecommended,
  isSelected,
  onSelect,
}: IRouteCardProps): React.JSX.Element {
  const arrivalEta: string | null =
    route.checkpoints.length > 0
      ? dayjs(route.checkpoints[route.checkpoints.length - 1].eta).format('MMM D, h:mm A')
      : null

  const overallRisk: TRiskLevel = route.severeMiles > 0
    ? 'severe'
    : route.highMiles > 50
    ? 'high'
    : route.riskScore < 1.5
    ? 'low'
    : 'moderate'

  return (
    <button
      className={clsx(
        'w-full rounded-lg border-2 p-4 text-left transition-all',
        isSelected
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-gray-50',
      )}
      type="button"
      onClick={onSelect}
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-900">
            Route {route.index + 1}
          </span>
          {isRecommended && (
            <span className="rounded-full bg-blue-600 px-2 py-0.5 text-xs font-medium text-white">
              Recommended
            </span>
          )}
        </div>
        <span
          className={clsx(
            'rounded-full px-2 py-0.5 text-xs font-medium text-white',
            RISK_BG_CLASSES[overallRisk],
          )}
        >
          {RISK_LABELS[overallRisk]}
        </span>
      </div>

      <p className="mb-3 text-xs text-gray-500">{route.summary}</p>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <Stat label="Distance" value={`${route.distanceMiles.toFixed(0)} mi`} />
        <Stat label="Duration" value={formatDuration(route.durationHours)} />
        <Stat label="Severe miles" value={`${route.severeMiles.toFixed(0)} mi`} />
        <Stat label="High-risk miles" value={`${route.highMiles.toFixed(0)} mi`} />
      </div>

      {arrivalEta && (
        <p className="mt-3 text-xs text-gray-500">
          ETA: <span className="font-medium text-gray-700">{arrivalEta}</span>
        </p>
      )}
    </button>
  )
}

function Stat({ label, value }: { label: string; value: string }): React.JSX.Element {
  return (
    <div>
      <p className="text-gray-400">{label}</p>
      <p className="font-medium text-gray-700">{value}</p>
    </div>
  )
}

function formatDuration(hours: number): string {
  const h: number = Math.floor(hours)
  const m: number = Math.round((hours - h) * 60)
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}
