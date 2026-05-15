/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'msu-green': '#18453B',
        'msu-green-dark': '#102E27',
        'msu-green-light': '#1f5749',
        'msu-gold': '#C89F2D',
        'status-healthy': '#2DA44E',
        'status-degraded': '#D97706',
        'status-down': '#CF222E',
        'base': '#FAFAFA',
        'surface': '#FFFFFF',
        'border': '#E5E7EB',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(0,0,0,0.08), 0 1px 2px -1px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 6px -1px rgba(0,0,0,0.08), 0 2px 4px -2px rgba(0,0,0,0.04)',
      },
    },
  },
  plugins: [],
}
