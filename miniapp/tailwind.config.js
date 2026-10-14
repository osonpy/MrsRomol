/** @type {import('tailwindcss').Config} */
// Mrs Romol palette — sampled from brand/MrsRomol.png (see brand/make_assets.py)
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        cream: { DEFAULT: '#FAF9F5', dark: '#F3EFE8' },
        rose: {
          50: '#FBF4F0',
          100: '#F6E7E0',
          200: '#EED3C8',
          300: '#E4B4A0',
          400: '#C29786',
          500: '#AE8373',
          600: '#986456', // primary — AA on cream and with white text
          700: '#7C4F43',
          800: '#5E3B32',
        },
        ink: { DEFAULT: '#3A2A25', soft: '#7A6862', faint: '#B5A69F' },
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        sans: ['"Manrope Variable"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(94, 59, 50, 0.06), 0 4px 16px rgba(94, 59, 50, 0.06)',
        sheet: '0 -8px 32px rgba(58, 42, 37, 0.12)',
      },
      keyframes: {
        'slide-up': { from: { transform: 'translateY(100%)' }, to: { transform: 'translateY(0)' } },
        'fade-in': { from: { opacity: 0 }, to: { opacity: 1 } },
        shimmer: { '100%': { transform: 'translateX(100%)' } },
      },
      animation: {
        'slide-up': 'slide-up 0.28s cubic-bezier(0.32, 0.72, 0, 1)',
        'fade-in': 'fade-in 0.2s ease-out',
      },
    },
  },
  plugins: [],
}
