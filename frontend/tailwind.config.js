/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0b1329',
          800: '#111d3d',
          700: '#18274f',
          600: '#22366b',
        },
        slate: {
          850: '#151e2e',
        },
        brand: {
          blue: '#0284c7',
          cyan: '#06b6d4',
          accent: '#38bdf8'
        }
      }
    },
  },
  plugins: [],
}
