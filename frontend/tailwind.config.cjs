module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#081018',
        slate: '#111827',
        mist: '#d9e2ec',
        signal: '#4ade80',
        amber: '#f59e0b',
      },
      boxShadow: {
        glow: '0 24px 80px rgba(74, 222, 128, 0.18)',
      },
    },
  },
  plugins: [],
};
