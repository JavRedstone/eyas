import { createTheme } from '@mui/material/styles'

export function createEyasTheme(mode) {
  const dark = mode === 'dark'

  // Yellow primary, blue secondary — Peregrine/Eyas palette
  const yellow = { main: dark ? '#f7d046' : '#d4a017', dark: dark ? '#c9a52e' : '#a07010', light: dark ? '#fae07a' : '#e8b830', contrast: dark ? '#0b1929' : '#0b1929' }
  const blue   = { main: dark ? '#4b9eff' : '#1565C0', dark: dark ? '#2d7dd2' : '#003c8f', contrast: '#ffffff' }
  const bg     = { default: dark ? '#0b1929' : '#eef2f7', paper: dark ? '#0f2338' : '#ffffff' }
  const text   = { primary: dark ? '#e5e1d8' : '#0d1b2a', secondary: dark ? '#7a8ea8' : '#4a6080' }
  const div    = dark ? '#1a3352' : '#c8d8ea'

  return createTheme({
    palette: {
      mode,
      primary:    { main: yellow.main, dark: yellow.dark, light: yellow.light, contrastText: yellow.contrast },
      secondary:  { main: blue.main, dark: blue.dark, contrastText: blue.contrast },
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
            backgroundColor: dark
              ? 'rgba(15,35,56,0.88)'
              : 'rgba(255,255,255,0.88)',
            backdropFilter: 'blur(8px)',
            borderBottom: `1px solid ${theme.palette.divider}`,
            boxShadow: 'none',
            color: theme.palette.text.primary,
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
              backgroundColor: dark ? 'rgba(11,25,41,0.6)' : theme.palette.background.default,
              fontWeight: 600,
              color: theme.palette.text.secondary,
            },
          }),
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: ({ theme }) => ({
            borderRadius: 8,
            '&:hover': { backgroundColor: dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)' },
          }),
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
