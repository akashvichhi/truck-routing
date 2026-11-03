import type { TRiskLevel } from '@src/types/route'

export const RISK_LABELS: Record<TRiskLevel, string> = {
  low:       'Low',
  moderate:  'Moderate',
  high:      'High',
  severe:    'Severe',
  no_travel: 'No Travel',
}

// Tailwind bg classes — must be full strings (not dynamic) for purge to keep them
export const RISK_BG_CLASSES: Record<TRiskLevel, string> = {
  low:       'bg-green-600',
  moderate:  'bg-yellow-500',
  high:      'bg-orange-600',
  severe:    'bg-red-600',
  no_travel: 'bg-violet-700',
}

export const RISK_TEXT_CLASSES: Record<TRiskLevel, string> = {
  low:       'text-green-700',
  moderate:  'text-yellow-700',
  high:      'text-orange-700',
  severe:    'text-red-700',
  no_travel: 'text-violet-700',
}

// Hex colours for Leaflet (cannot use Tailwind classes in JS context)
export const RISK_HEX: Record<TRiskLevel, string> = {
  low:       '#16a34a',
  moderate:  '#ca8a04',
  high:      '#ea580c',
  severe:    '#dc2626',
  no_travel: '#7c3aed',
}

// Polyline colours for each route index (up to 3 routes)
export const ROUTE_COLORS: string[] = ['#2563eb', '#0891b2', '#7c3aed']

// Heatmap gradient: risk score 1 (low) → 5 (no_travel)
export const HEATMAP_GRADIENT: Record<string, string> = {
  '0.0': '#16a34a',
  '0.3': '#ca8a04',
  '0.5': '#ea580c',
  '0.7': '#dc2626',
  '1.0': '#7c3aed',
}

export const MAX_FORECAST_HOURS: number = 48
