import { createTheme } from '@mui/material/styles'

export function createEyasTheme(mode) {
  const dark = mode === 'dark'

  // Dark:  yellow primary on navy  — Peregrine plumage
  // Light: blue primary on warm yellow — inverted palette
  const primary = dark
    ? { main: '#f7d046', dark: '#c9a52e', light: '#fae07a', contrast: '#0b1929' }
    : { main: '#1565C0', dark: '#003c8f', light: '#4d8cda', contrast: '#ffffff' }

  const secondary = dark
    ? { main: '#4b9eff', dark: '#2d7dd2', contrast: '#ffffff' }
    : { main: '#d4a017', dark: '#a07010', contrast: '#0b1929' }

  const bg = dark
    ? { default: '#0b1929', paper: '#0f2338' }
    : { default: '#fef9e7', paper: '#ffffff' }   // warm yellow ground, white cards

  const text = dark
    ? { primary: '#e5e1d8', secondary: '#7a8ea8' }
    : { primary: '#0d1b2a', secondary: '#4a5e78' }

  const div = dark ? '#1a3352' : '#dfc85e'   // navy rule / golden rule

  // AppBar tint: translucent navy in dark, translucent warm-yellow in light
  const appBarBg = dark ? 'rgba(15,35,56,0.90)' : 'rgba(254,248,220,0.92)'
  const appBarColor = dark ? '#e5e1d8' : '#0d1b2a'

  return createTheme({
    palette: {
      mode,
      primary:    { main: primary.main, dark: primary.dark, light: primary.light, contrastText: primary.contrast },
      secondary:  { main: secondary.main, dark: secondary.dark, contrastText: secondary.contrast },
      background: bg,
      text,
      success: { main: '#34D399' },
      warning: { main: '#f7d046' },
      error:   { main: '#F87171' },
      divider: div,
    },
    shape: { borderRadius: 12 },
    typography: {
      fontFamily: '"Inter", "ui-sans-serif", system-ui, sans-serif',
      button: { textTransform: 'none', fontWeight: 600 },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: (theme) => ({
          body: {
            scrollbarWidth: 'thin',
            scrollbarColor: `${theme.palette.divider} ${theme.palette.background.paper}`,
            '&::-webkit-scrollbar': { width: 5, height: 5 },
            '&::-webkit-scrollbar-track': { background: theme.palette.background.paper },
            '&::-webkit-scrollbar-thumb': { background: theme.palette.divider, borderRadius: 9999 },
            '&::-webkit-scrollbar-thumb:hover': { background: theme.palette.primary.dark },
          },
        }),
      },
      MuiPaper: {
        defaultProps: { elevation: 0 },
        styleOverrides: {
          root: ({ theme }) => ({
            backgroundImage: 'none',
            border: `1px solid ${theme.palette.divider}`,
          }),
        },
      },
      MuiButton: {
        defaultProps: { disableElevation: true },
        styleOverrides: {
          root: { borderRadius: 8 },
          containedPrimary: ({ theme }) => ({
            color: theme.palette.primary.contrastText,
            '&:hover': { backgroundColor: theme.palette.primary.dark },
            boxShadow: `0 4px 14px ${theme.palette.primary.main}44`,
          }),
          containedSecondary: ({ theme }) => ({
            '&:hover': { backgroundColor: theme.palette.secondary.dark },
          }),
        },
      },
      MuiTab: {
        styleOverrides: {
          root: { textTransform: 'none', fontWeight: 500, minHeight: 44, fontSize: '0.75rem' },
        },
      },
      MuiTabs: {
        styleOverrides: {
          indicator: ({ theme }) => ({ backgroundColor: theme.palette.primary.main, height: 2 }),
          scrollButtons: ({ theme }) => ({ color: theme.palette.text.secondary }),
        },
      },
      MuiChip: {
        styleOverrides: { root: { borderRadius: 6, fontSize: '0.7rem' } },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: ({ theme }) => ({
            fontSize: '0.875rem',
            '& fieldset': { borderColor: theme.palette.divider },
            '&:hover fieldset': { borderColor: `${theme.palette.primary.light} !important` },
            '&.Mui-focused fieldset': { borderColor: `${theme.palette.primary.main} !important` },
          }),
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: ({ theme }) => ({ borderRadius: 4, backgroundColor: theme.palette.divider }),
          bar: ({ theme }) => ({ borderRadius: 4, backgroundColor: theme.palette.primary.main }),
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: ({ theme }) => ({
            backgroundImage: 'none',
            backgroundColor: appBarBg,
            backdropFilter: 'blur(8px)',
            borderBottom: `1px solid ${theme.palette.divider}`,
            boxShadow: 'none',
            color: appBarColor,
          }),
        },
      },
      MuiTableCell: {
        styleOverrides: {
          root: ({ theme }) => ({ borderColor: theme.palette.divider, fontSize: '0.75rem' }),
        },
      },
      MuiTableHead: {
        styleOverrides: {
          root: ({ theme }) => ({
            '& .MuiTableCell-root': {
              backgroundColor: dark ? 'rgba(11,25,41,0.6)' : 'rgba(254,240,160,0.35)',
              fontWeight: 600,
              color: theme.palette.text.secondary,
            },
          }),
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            '&:hover': { backgroundColor: dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)' },
          },
        },
      },
      MuiDivider: {
        styleOverrides: { root: ({ theme }) => ({ borderColor: theme.palette.divider }) },
      },
      MuiSelect: {
        styleOverrides: {
          icon: ({ theme }) => ({ color: theme.palette.text.secondary }),
        },
      },
      MuiMenuItem: {
        styleOverrides: { root: { fontSize: '0.875rem' } },
      },
      MuiToggleButton: {
        styleOverrides: {
          root: ({ theme }) => ({
            borderColor: `${theme.palette.divider} !important`,
            '&.Mui-selected': {
              backgroundColor: `${theme.palette.primary.main}18`,
              borderColor: `${theme.palette.primary.main} !important`,
              color: theme.palette.primary.main,
              '&:hover': { backgroundColor: `${theme.palette.primary.main}28` },
            },
          }),
        },
      },
    },
  })
}
