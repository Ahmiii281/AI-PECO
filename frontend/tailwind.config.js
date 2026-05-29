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
        black: '#000000',
        white: '#FFFFFF',
        green: {
          500: '#00FF41',
          600: '#00CC33',
        },
        zinc: {
          900: '#0A0A0A',
          800: '#1A1A1A',
          700: '#333333',
        }
      },
      boxShadow: {
        'glow': '0 0 10px rgba(0, 255, 65, 0.4)',
        'glow-lg': '0 0 20px rgba(0, 255, 65, 0.6)',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
