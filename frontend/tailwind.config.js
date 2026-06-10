/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        slate: {
          950: '#0F172A',
          900: '#111D2E',
          850: '#132035',
          800: '#1A2D45',
          700: '#1E3A2F',
        },
        green: {
          300: '#86EFAC',
          400: '#4ADE80',
          500: '#22C55E',   // Accent Green
          600: '#16A34A',   // Primary Green
          700: '#15803D',
          800: '#166534',   // Dark Green
          900: '#14532D',
        },
        accent: {
          DEFAULT: '#16A34A',
          light: '#22C55E',
          dark: '#166534',
          soft: '#DCFCE7',
        },
        info:    '#38BDF8',
        success: '#22C55E',
        warning: '#F59E0B',
        danger:  '#EF4444',
      },
      boxShadow: {
        'glow':     '0 0 18px rgba(22, 163, 74, 0.20)',
        'glow-lg':  '0 0 32px rgba(34, 197, 94, 0.28)',
        'glow-sm':  '0 0 10px rgba(22, 163, 74, 0.14)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'green-gradient': 'linear-gradient(135deg, #16A34A, #166534)',
        'green-glow':     'radial-gradient(ellipse at top left, rgba(22,163,74,0.12), transparent 50%)',
      },
    },
  },
  plugins: [],
}
