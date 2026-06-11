/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:      '#0e2946',  // dark slate blue — dominant plumage
        surface: '#142d4f',
        panel:   '#1f2833',  // charcoal — head stripes / wing contrast
        border:  '#2e4060',
        accent:  '#f7d046',  // bright yellow — cere / talons
        'accent-dim': '#c9a52e',
        text:    '#e5e1d8',  // soft cream — underbelly
        muted:   '#7a8ea8',
        success: '#34D399',
        warning: '#f7d046',
        danger:  '#F87171',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow':  'spin 3s linear infinite',
      },
    },
  },
  plugins: [],
}
