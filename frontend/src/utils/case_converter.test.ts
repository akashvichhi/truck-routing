import { describe, it, expect } from 'vitest'
import { keysToCamel, keysToSnake } from './case_converter'

describe('keysToCamel', () => {
  it('converts snake_case keys to camelCase', () => {
    expect(keysToCamel({ wind_mph: 10, rain_in_hr: 0.1 })).toEqual({
      windMph: 10,
      rainInHr: 0.1,
    })
  })

  it('recurses into nested objects', () => {
    const input = { route_data: { distance_miles: 100 } }
    expect(keysToCamel(input)).toEqual({ routeData: { distanceMiles: 100 } })
  })

  it('recurses into arrays', () => {
    const input = [{ risk_level: 'low' }, { risk_level: 'high' }]
    expect(keysToCamel(input)).toEqual([{ riskLevel: 'low' }, { riskLevel: 'high' }])
  })

  it('leaves primitive values unchanged', () => {
    expect(keysToCamel('hello')).toBe('hello')
    expect(keysToCamel(42)).toBe(42)
    expect(keysToCamel(null)).toBe(null)
  })
})

describe('keysToSnake', () => {
  it('converts camelCase keys to snake_case', () => {
    expect(keysToSnake({ windMph: 10, rainInHr: 0.1 })).toEqual({
      wind_mph: 10,
      rain_in_hr: 0.1,
    })
  })

  it('recurses into nested objects', () => {
    const input = { routeData: { distanceMiles: 100 } }
    expect(keysToSnake(input)).toEqual({ route_data: { distance_miles: 100 } })
  })
})
