import { definePreset } from '@primevue/themes'
import Aura from '@primevue/themes/aura'

export const WealthsimpleTheme = definePreset(Aura, {
  semantic: {
    primary: {
      50:  '{teal.50}',
      100: '{teal.100}',
      200: '{teal.200}',
      300: '{teal.300}',
      400: '{teal.400}',
      500: '#00C4A0',
      600: '#00A888',
      700: '#008C72',
      800: '#006F5A',
      900: '#005444',
      950: '#003830',
    },
    colorScheme: {
      light: {
        surface: {
          0:   '#ffffff',
          50:  '#F7F8FA',
          100: '#F0F1F3',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          900: '#111827',
          950: '#030712',
        },
      },
    },
  },
})
