import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        risk: {
          low:       '#16a34a', // green-600
          moderate:  '#ca8a04', // yellow-600
          high:      '#ea580c', // orange-600
          severe:    '#dc2626', // red-600
          no_travel: '#7c3aed', // violet-600
        },
      },
    },
  },
  plugins: [],
}

export default config
