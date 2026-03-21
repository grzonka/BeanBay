import { createTheme } from '@mui/material/styles';
import { commonThemeOptions } from './common';

export const espressoDark = createTheme({
  ...commonThemeOptions,
  palette: {
    mode: 'dark',
    primary: { main: '#c4956a' },
    secondary: { main: '#d4a574' },
    background: { default: '#1a1210', paper: '#2d1f1a' },
    text: { primary: '#e8dcc8', secondary: '#a89880' },
    error: { main: '#d4756a' },
    warning: { main: '#d4a56a' },
    success: { main: '#7ab57a' },
    divider: 'rgba(196,149,106,0.15)',
  },
});
