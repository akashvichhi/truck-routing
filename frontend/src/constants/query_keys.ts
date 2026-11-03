import type { IRouteRequest } from '@src/types/route'

export const routeKeys = {
  all: ['routes'] as const,
  result: (params: IRouteRequest) => ['routes', params] as const,
}
