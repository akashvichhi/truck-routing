import axios from 'axios'

import { API_URL } from '@src/config/env'
import { keysToCamel, keysToSnake } from '@src/utils/case_converter'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Convert request body keys from camelCase → snake_case
apiClient.interceptors.request.use((config) => {
  if (config.data) {
    config.data = keysToSnake(config.data)
  }
  return config
})

// Convert response body keys from snake_case → camelCase
apiClient.interceptors.response.use(
  (response) => {
    response.data = keysToCamel(response.data)
    return response
  },
  (error) => {
    const data: Record<string, unknown> = error.response?.data ?? {}
    const base: string = typeof data.error === 'string' ? data.error : (error.message ?? 'An unexpected error occurred')

    // Append field-level detail messages when present (e.g. validation errors)
    let message = base
    if (data.details && typeof data.details === 'object') {
      const fieldMsgs = Object.values(data.details as Record<string, string[]>)
        .flat()
        .filter((m): m is string => typeof m === 'string')
      if (fieldMsgs.length > 0) {
        message = `${base}: ${fieldMsgs.join('; ')}`
      }
    }

    return Promise.reject(new Error(message))
  },
)

export default apiClient
