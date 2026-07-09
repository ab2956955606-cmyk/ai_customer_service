/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif']
      },
      colors: {
        ink: '#172026',
        mist: '#eef3f2',
        ocean: '#0f766e',
        ember: '#b45309',
        rosewood: '#be123c'
      }
    }
  },
  plugins: []
};
