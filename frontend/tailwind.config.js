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
          900: '#111827',
          850: '#1E293B',
          800: '#273449',
          700: '#334155',
        },
        cyan: {
          400: '#67E8F9',
          500: '#06B6D4',
          600: '#0E7490',
        },
        accent: {
          DEFAULT: '#06B6D4',
          light: '#67E8F9',
          dim: '#0E7490',
        },
        info: '#38BDF8',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
      },
      boxShadow: {
        glow: '0 0 18px rgba(6, 182, 212, 0.18)',
        'glow-lg': '0 0 28px rgba(6, 182, 212, 0.24)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
