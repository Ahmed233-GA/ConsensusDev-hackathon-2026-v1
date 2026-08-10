/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      colors: {
        ink: {
          950: '#070a14',
          900: '#0b0f1c',
          850: '#0f1424',
          800: '#131a2e',
          700: '#1a2340',
          600: '#243056',
          500: '#34406b',
          400: '#4a578a',
          300: '#6b7aa8',
          200: '#9aa6c8',
          100: '#c4cce0',
        },
        brand: {
          500: '#10a2f4',
          400: '#3bb6ff',
          300: '#6ac8ff',
        },
        teal: {
          500: '#14b8a6',
          400: '#2dd4bf',
        },
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'pulse-ring': {
          '0%': { transform: 'scale(0.8)', opacity: '0.6' },
          '100%': { transform: 'scale(2.4)', opacity: '0' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        'scan-line': {
          '0%': { top: '0%' },
          '100%': { top: '100%' },
        },
        'spin-slow': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        'bounce-dot': {
          '0%, 80%, 100%': { transform: 'scale(0.6)', opacity: '0.4' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.5s cubic-bezier(0.16,1,0.3,1) both',
        'slide-in': 'slide-in 0.4s ease-out both',
        'pulse-ring': 'pulse-ring 1.8s ease-out infinite',
        shimmer: 'shimmer 2s linear infinite',
        'scan-line': 'scan-line 2s ease-in-out infinite alternate',
        'spin-slow': 'spin-slow 3s linear infinite',
        'bounce-dot': 'bounce-dot 1.2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
