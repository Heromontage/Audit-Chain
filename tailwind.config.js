/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./frontend/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        brand: {
          purple: '#6c2bd9',
          indigo: '#4f46e5',
          violet: '#A855F7',
          lavender: '#C084FC',
          orange: '#F97316',
        },
      },
    },
  },
  plugins: [],
};