import { createTheme } from '@mui/material/styles';
import { commonThemeOptions } from './common';

export const craftLight = createTheme({
  ...commonThemeOptions,
  palette: {
    mode: 'light',
    primary: { main: '#8b5e3c' },
    secondary: { main: '#6b4c2a' },
    background: { default: '#faf8f5', paper: '#ffffff' },
    text: { primary: '#3d2b22', secondary: '#7a6a5a' },
    error: { main: '#c0392b' },
    warning: { main: '#d4a56a' },
    success: { main: '#27ae60' },
    divider: '#e0d6ca',
  },
});
