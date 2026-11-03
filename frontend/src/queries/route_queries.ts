import { useMutation } from '@tanstack/react-query'

import { fetchRoutes } from '@src/api/route_api'
import type { IRouteRequest, IRoutesResponse } from '@src/types/route'

// Using mutation (not query) because the user triggers a POST with form data
export function useRoutesMutation(): ReturnType<
  typeof useMutation<IRoutesResponse, Error, IRouteRequest>
> {
  return useMutation<IRoutesResponse, Error, IRouteRequest>({
    mutationFn: fetchRoutes,
  })
}
