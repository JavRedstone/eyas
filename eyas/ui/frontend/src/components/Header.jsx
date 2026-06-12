import { Sun, Moon } from 'lucide-react'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import IconButton from '@mui/material/IconButton'
import Tooltip from '@mui/material/Tooltip'
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup'
import ToggleButton from '@mui/material/ToggleButton'
import Divider from '@mui/material/Divider'
import { t } from '../i18n.js'

const LANGUAGES = [
  { value: 'English', label: 'EN' },
  { value: '한국어',   label: '한' },
]

export default function Header({ language, colorMode, onToggleColorMode, onSwitchLanguage }) {
  const dark = colorMode === 'dark'
  return (
    <AppBar position="sticky">
      <Toolbar sx={{ minHeight: '52px !important', px: 2.5, gap: 1.5 }}>
        {/* Logo mark */}
        <Box sx={{
          width: 26, height: 26, borderRadius: 1.5,
          bgcolor: 'primary.main',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'primary.contrastText', opacity: 0.85 }} />
        </Box>

        <Typography variant="subtitle1" fontWeight={700} sx={{ letterSpacing: '-0.01em', color: 'text.primary' }}>
          Eyas
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ display: { xs: 'none', md: 'block' } }}>
          {t(language, 'header.subtitle')}
        </Typography>

        <Box sx={{ flexGrow: 1 }} />

        {/* Language quick-switch */}
        <ToggleButtonGroup
          value={language}
          exclusive
          onChange={(_, v) => v && onSwitchLanguage?.(v)}
          size="small"
          sx={{
            height: 28,
            '& .MuiToggleButton-root': {
              px: 1.25, py: 0,
              fontSize: '0.7rem',
              fontWeight: 600,
              border: '1px solid',
              borderColor: 'divider',
              color: 'text.secondary',
              lineHeight: 1,
              '&.Mui-selected': {
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
                borderColor: 'primary.main',
                '&:hover': { bgcolor: 'primary.dark', borderColor: 'primary.dark' },
              },
              '&:not(.Mui-selected):hover': { bgcolor: 'action.hover' },
            },
          }}>
          {LANGUAGES.map(l => (
            <ToggleButton key={l.value} value={l.value}>{l.label}</ToggleButton>
          ))}
        </ToggleButtonGroup>

        <Divider orientation="vertical" flexItem sx={{ mx: 0.5, my: 1 }} />

        {/* Dark/light toggle */}
        <Tooltip title={dark ? 'Light mode' : 'Dark mode'}>
          <IconButton size="small" onClick={onToggleColorMode} sx={{ color: 'text.secondary' }}>
            {dark ? <Sun size={15} /> : <Moon size={15} />}
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  )
}
