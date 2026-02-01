/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        burgundy: '#780000',
        crimson: '#C1121F',
        cream: '#FDF0D5',
        navy: '#003049',
        steel: '#669BBC',
      },
    },
  },
  plugins: [],
}
