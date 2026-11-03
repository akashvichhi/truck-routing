import apiClient from '@src/api/api_client'
import { ROUTES_ENDPOINT } from '@src/constants/api_endpoints'
import type { IRouteRequest, IRoutesResponse } from '@src/types/route'

export async function fetchRoutes(params: IRouteRequest): Promise<IRoutesResponse> {
  const response = await apiClient.post<{ data: IRoutesResponse }>(ROUTES_ENDPOINT, params)
  return response.data.data
}
