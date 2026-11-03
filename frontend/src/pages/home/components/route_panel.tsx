import { RouteCard } from '@src/pages/home/components/route_card'
import type { IRoute } from '@src/types/route'

interface IRoutePanelProps {
  routes: IRoute[]
  recommendedIndex: number
  selectedIndex: number
  onSelectRoute: (index: number) => void
}

export function RoutePanel({
  routes,
  recommendedIndex,
  selectedIndex,
  onSelectRoute,
}: IRoutePanelProps): React.JSX.Element {
  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
        Route Options
      </h2>
      {routes.map((route: IRoute) => (
        <RouteCard
          isRecommended={route.index === recommendedIndex}
          isSelected={route.index === selectedIndex}
          key={route.index}
          route={route}
          onSelect={(): void => onSelectRoute(route.index)}
        />
      ))}
    </div>
  )
}
