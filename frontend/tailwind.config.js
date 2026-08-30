/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        pro: {
          light: '#eff6ff',
          DEFAULT: '#3b82f6',
          dark: '#1d4ed8',
        },
        con: {
          light: '#fff1f2',
          DEFAULT: '#f43f5e',
          dark: '#be123c',
        }
      }
    },
  },
  plugins: [],
}