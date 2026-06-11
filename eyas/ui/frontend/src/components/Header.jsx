import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'

export default function Header({ language }) {
  return (
    <AppBar position="sticky">
      <Toolbar sx={{ minHeight: '52px !important', px: 2.5, gap: 1.5 }}>
        <Box sx={{
          width: 28, height: 28, borderRadius: 1.5,
          border: '1px solid', borderColor: 'rgba(247,208,70,0.3)',
          bgcolor: 'rgba(247,208,70,0.08)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'primary.main' }} />
        </Box>
        <Typography variant="subtitle1" fontWeight={600} sx={{ letterSpacing: '-0.01em' }}>
          Eyas
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
          AI Security Camera Agent
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
          {language}
        </Typography>
      </Toolbar>
    </AppBar>
  )
}
