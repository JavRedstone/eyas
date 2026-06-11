/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:      '#0F1117',
        surface: '#161B2C',
        panel:   '#1E2436',
        border:  '#2A3050',
        accent:  '#E8682A',
        'accent-dim': '#B84E1C',
        text:    '#EEF0F8',
        muted:   '#6B728E',
        success: '#34D399',
        warning: '#FBBF24',
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
