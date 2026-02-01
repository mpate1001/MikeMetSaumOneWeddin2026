/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Wedding color palette
        'space-indigo': '#2B2D42',    // Dark blue-black
        'lavender-grey': '#8D99AE',   // Muted purple-grey
        'platinum': '#EDF2F4',        // Silver-white
        'strawberry': '#EF233C',      // Vibrant red
        'crimson': '#D80032',         // Classic deep red
        // Keep old names as aliases for compatibility
        burgundy: '#D80032',
        navy: '#2B2D42',
        steel: '#8D99AE',
        cream: '#EDF2F4',
      },
    },
  },
  plugins: [],
}
