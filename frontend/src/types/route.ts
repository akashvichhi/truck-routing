export type TRiskLevel = 'low' | 'moderate' | 'high' | 'severe' | 'no_travel'

export interface IGeocodeResult {
  label: string
  lat: number
  lng: number
}

export interface ICheckpoint {
  lat: number
  lng: number
  mile: number
  eta: string
  windMph: number
  rainInHr: number
  snowInHr: number
  riskLevel: TRiskLevel
}

export interface IRoute {
  index: number
  summary: string
  distanceMiles: number
  durationHours: number
  riskScore: number
  severeMiles: number
  highMiles: number
  geometry: [number, number][]
  checkpoints: ICheckpoint[]
}

export interface IHeatmapPoint {
  lat: number
  lng: number
  riskValue: number
  forecastHour: number
}

export interface IRouteRequest {
  origin: string
  destination: string
  departureDatetime: string
  loadWeightLbs: number
}

export interface IRoutesResponse {
  recommendedRouteIndex: number
  routes: IRoute[]
  heatmapPoints: IHeatmapPoint[]
}
