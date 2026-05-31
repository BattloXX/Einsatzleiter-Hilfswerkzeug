/** Tailwind-Konfiguration fuer einsatzleiter.cloud.
 *
 * Farben, Typografie, Spacing und Radius sind aus dem Stitch-Design-System
 * "Emergency Operations System" uebernommen. Wenn das Design veraendert
 * wird, hier zentral aktualisieren.
 */
module.exports = {
  darkMode: 'class',
  content: [
    './app/templates/**/*.html',
    './app/static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        // Stitch "Emergency Operations System" palette
        'surface': '#0b1326',
        'surface-dim': '#0b1326',
        'surface-bright': '#31394d',
        'surface-container-lowest': '#060e20',
        'surface-container-low': '#131b2e',
        'surface-container': '#171f33',
        'surface-container-high': '#222a3d',
        'surface-container-highest': '#2d3449',
        'surface-variant': '#2d3449',
        'on-surface': '#dae2fd',
        'on-surface-variant': '#e4beba',
        'inverse-surface': '#dae2fd',
        'inverse-on-surface': '#283044',
        'outline': '#ab8985',
        'outline-variant': '#5b403d',
        'surface-tint': '#ffb3ac',
        'primary': '#ffb3ac',
        'on-primary': '#680008',
        'primary-container': '#d32f2f',
        'on-primary-container': '#fff2f0',
        'inverse-primary': '#ba1a20',
        'secondary': '#bcc7de',
        'on-secondary': '#263143',
        'secondary-container': '#3e495d',
        'on-secondary-container': '#aeb9d0',
        'tertiary': '#adc6ff',
        'on-tertiary': '#002e6a',
        'tertiary-container': '#156bde',
        'on-tertiary-container': '#f2f4ff',
        'error': '#ffb4ab',
        'on-error': '#690005',
        'error-container': '#93000a',
        'on-error-container': '#ffdad6',
        'background': '#0b1326',
        'on-background': '#dae2fd',
        // Brand red (FF Wolfurt) — fuer Logo-Akzent + Alarm-Indikatoren
        'brand-red': '#d42225',
        'brand-red-dark': '#a5161a',
        'brand-red-light': '#e8403f',
        // Semantik (Status, Warnungen, Erfolge)
        'success': '#18a957',
        'warning': '#f2b02e',
        'danger': '#d83030',
        'info': '#1877f2',
      },
      fontFamily: {
        sans: ['"Hanken Grotesk"', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
        'headline': ['"Hanken Grotesk"', 'sans-serif'],
        'label-caps': ['"JetBrains Mono"', 'monospace'],
      },
      fontSize: {
        'display-lg': ['32px', { lineHeight: '40px', letterSpacing: '-0.02em', fontWeight: '700' }],
        'headline-md': ['20px', { lineHeight: '28px', fontWeight: '600' }],
        'headline-sm': ['16px', { lineHeight: '24px', fontWeight: '600' }],
        'body-lg': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'body-sm': ['14px', { lineHeight: '20px', fontWeight: '400' }],
        'label-caps': ['12px', { lineHeight: '16px', letterSpacing: '0.05em', fontWeight: '600' }],
        'status-badge': ['11px', { lineHeight: '12px', fontWeight: '700' }],
      },
      borderRadius: {
        'DEFAULT': '0.25rem',
        'sm': '0.125rem',
        'md': '0.375rem',
        'lg': '0.5rem',
        'xl': '0.75rem',
        'full': '9999px',
      },
      spacing: {
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
        'gutter': '12px',
        'app-padding': '20px',
        'column-width': '320px',
        'topnav-h': '64px',
      },
      boxShadow: {
        'card': '0 1px 2px rgba(0,0,0,0.4)',
        'modal': '0 10px 40px rgba(0,0,0,0.6)',
        'drag': '0 8px 24px rgba(0,0,0,0.5)',
      },
      keyframes: {
        'lu-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.55' },
        },
      },
      animation: {
        'lu-pulse': 'lu-pulse 1.6s ease-in-out infinite',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries'),
  ],
};
