import { Sun, Moon } from 'lucide-react'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'
import IconButton from '@mui/material/IconButton'
import Tooltip from '@mui/material/Tooltip'

export default function Header({ language, colorMode, onToggleColorMode }) {
  const dark = colorMode === 'dark'
  return (
    <AppBar position="sticky">
      <Toolbar sx={{ minHeight: '52px !important', px: 2.5, gap: 1.5 }}>
        <Box sx={{
          width: 28, height: 28, borderRadius: 1.5,
          border: '1px solid', borderColor: 'primary.light',
          bgcolor: 'primary.main',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          opacity: 0.9,
        }}>
          <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'secondary.main' }} />
        </Box>
        <Typography variant="subtitle1" fontWeight={700} sx={{ letterSpacing: '-0.01em', color: 'text.primary' }}>
          Eyas
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
          AI Security Camera Agent
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace', mr: 0.5 }}>
          {language}
        </Typography>
        <Tooltip title={dark ? 'Switch to light mode' : 'Switch to dark mode'}>
          <IconButton size="small" onClick={onToggleColorMode} sx={{ color: 'text.secondary' }}>
            {dark ? <Sun size={16} /> : <Moon size={16} />}
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  )
}
