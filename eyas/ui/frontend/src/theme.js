import { createTheme } from '@mui/material/styles'

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#f7d046',
      dark: '#c9a52e',
      contrastText: '#0e2946',
    },
    secondary: {
      main: '#7a8ea8',
      contrastText: '#e5e1d8',
    },
    background: {
      default: '#0e2946',
      paper: '#1f2833',
    },
    text: {
      primary: '#e5e1d8',
      secondary: '#7a8ea8',
    },
    success: { main: '#34D399' },
    warning: { main: '#f7d046' },
    error: { main: '#F87171' },
    divider: '#2e4060',
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: '"Inter", "ui-sans-serif", system-ui, sans-serif',
    button: { textTransform: 'none', fontWeight: 600 },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: 'thin',
          scrollbarColor: '#2e4060 #1f2833',
          '&::-webkit-scrollbar': { width: 5, height: 5 },
          '&::-webkit-scrollbar-track': { background: '#1f2833' },
          '&::-webkit-scrollbar-thumb': { background: '#2e4060', borderRadius: 9999 },
          '&::-webkit-scrollbar-thumb:hover': { background: '#3e5278' },
        },
      },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: { backgroundImage: 'none', border: '1px solid #2e4060' },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { borderRadius: 8 },
        containedPrimary: {
          '&:hover': { backgroundColor: '#c9a52e' },
          boxShadow: '0 4px 14px rgba(247,208,70,0.2)',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: { textTransform: 'none', fontWeight: 500, minHeight: 44, fontSize: '0.75rem' },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: { backgroundColor: '#f7d046', height: 2 },
        scrollButtons: { color: '#7a8ea8' },
      },
    },
    MuiChip: {
      styleOverrides: { root: { borderRadius: 6, fontSize: '0.7rem' } },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          fontSize: '0.875rem',
          '& fieldset': { borderColor: '#2e4060' },
          '&:hover fieldset': { borderColor: '#3e5278 !important' },
          '&.Mui-focused fieldset': { borderColor: '#f7d046 !important' },
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: { borderRadius: 4, backgroundColor: '#2e4060' },
        bar: { borderRadius: 4, backgroundColor: '#f7d046' },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: 'rgba(31,40,51,0.85)',
          backdropFilter: 'blur(8px)',
          borderBottom: '1px solid #2e4060',
          boxShadow: 'none',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: { root: { borderColor: '#2e4060', fontSize: '0.75rem' } },
    },
    MuiTableHead: {
      styleOverrides: { root: { '& .MuiTableCell-root': { backgroundColor: 'rgba(20,45,79,0.5)', fontWeight: 600, color: '#7a8ea8' } } },
    },
    MuiIconButton: {
      styleOverrides: { root: { borderRadius: 8, '&:hover': { backgroundColor: 'rgba(255,255,255,0.06)' } } },
    },
    MuiDivider: {
      styleOverrides: { root: { borderColor: '#2e4060' } },
    },
    MuiSelect: {
      styleOverrides: {
        icon: { color: '#7a8ea8' },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: { fontSize: '0.875rem' },
      },
    },
  },
})

export default theme
