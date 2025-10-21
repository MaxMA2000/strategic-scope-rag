/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#1a1b1e',
        'bg-secondary': '#2b2d31',
        'bg-tertiary': '#383a40',
        'bg-hover': '#404249',
        'text-primary': '#f2f3f5',
        'text-secondary': '#b5bac1',
        'text-muted': '#80848e',
        'accent-green': '#23a55a',
        'accent-teal': '#1abc9c',
        'border-color': '#3f4147',
        'border-hover': '#4e5058',
      },
    },
  },
  plugins: [],
}

