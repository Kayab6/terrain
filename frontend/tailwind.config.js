/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        terrain: {
          dark: '#1a1d1a',
          brown: '#4a3f35',
          green: '#2d4a22'
        }
      }
    },
  },
  plugins: [],
}
