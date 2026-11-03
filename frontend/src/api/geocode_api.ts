import apiClient from '@src/api/api_client'
import { GEOCODE_ENDPOINT } from '@src/constants/api_endpoints'
import type { IGeocodeResult } from '@src/types/route'

export async function fetchAddressSuggestions(query: string): Promise<IGeocodeResult[]> {
  const resp = await apiClient.get<IGeocodeResult[]>(GEOCODE_ENDPOINT, {
    params: { q: query },
  })
  return resp.data
}
