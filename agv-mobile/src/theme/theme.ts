import { MD3LightTheme } from 'react-native-paper';

export const theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#2563eb', // Blue-600
    secondary: '#dc2626', // Red-600
    accent: '#f59e0b', // Amber-500
    background: '#f8fafc',
    surface: '#ffffff',
    text: '#1e293b',
    placeholder: '#64748b',
    error: '#dc2626',
  },
};