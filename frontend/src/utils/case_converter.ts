type PlainObject = Record<string, unknown>

function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, (c: string) => `_${c.toLowerCase()}`)
}

function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_: string, c: string) => c.toUpperCase())
}

function convertKeys(obj: unknown, converter: (k: string) => string): unknown {
  if (Array.isArray(obj)) {
    return obj.map((item: unknown) => convertKeys(item, converter))
  }
  if (obj !== null && typeof obj === 'object' && !(obj instanceof FormData) && !(obj instanceof Blob)) {
    const result: PlainObject = {}
    for (const [key, value] of Object.entries(obj as PlainObject)) {
      result[converter(key)] = convertKeys(value, converter)
    }
    return result
  }
  return obj
}

export function keysToCamel(obj: unknown): unknown {
  return convertKeys(obj, toCamelCase)
}

export function keysToSnake(obj: unknown): unknown {
  return convertKeys(obj, toSnakeCase)
}
