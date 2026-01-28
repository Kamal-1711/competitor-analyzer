/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Premium dark theme colors
                dark: {
                    900: '#0a0a0f',
                    800: '#12121a',
                    700: '#1a1a24',
                    600: '#22222e',
                    500: '#2a2a38',
                },
                // Vibrant accent colors
                accent: {
                    purple: '#8b5cf6',
                    blue: '#3b82f6',
                    cyan: '#06b6d4',
                    green: '#10b981',
                    orange: '#f97316',
                    pink: '#ec4899',
                    red: '#ef4444',
                },
                // Glass effect colors
                glass: {
                    white: 'rgba(255, 255, 255, 0.2)',
                    border: 'rgba(255, 255, 255, 0.3)',
                }
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'gradient-mesh': 'linear-gradient(135deg, #8b5cf6 0%, #3b82f6 50%, #06b6d4 100%)',
                'gradient-warm': 'linear-gradient(135deg, #f97316 0%, #ec4899 100%)',
                'gradient-cool': 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                'gradient-success': 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
            },
            boxShadow: {
                'glow-purple': '0 0 20px rgba(139, 92, 246, 0.3)',
                'glow-blue': '0 0 20px rgba(59, 130, 246, 0.3)',
                'glow-cyan': '0 0 20px rgba(6, 182, 212, 0.3)',
                'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'gradient': 'gradient 8s ease infinite',
                'float': 'float 6s ease-in-out infinite',
                'scan': 'scan 2s ease-in-out infinite',
            },
            keyframes: {
                gradient: {
                    '0%, 100%': { backgroundPosition: '0% 50%' },
                    '50%': { backgroundPosition: '100% 50%' },
                },
                float: {
                    '0%, 100%': { transform: 'translateY(0px)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
                scan: {
                    '0%': { transform: 'translateX(-100%)' },
                    '100%': { transform: 'translateX(100%)' },
                }
            },
            backdropBlur: {
                xs: '2px',
            },
        },
    },
    plugins: [],
}
