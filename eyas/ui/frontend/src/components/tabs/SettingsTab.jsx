import { useState } from 'react'
import { Save, Globe } from 'lucide-react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import ToggleButton from '@mui/material/ToggleButton'
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup'

const LANGUAGES = ['English', '한국어']

export default function SettingsTab({ client, language, setLanguage }) {
  const [local, setLocal]   = useState(language)
  const [status, setStatus] = useState('')

  async function save() {
    if (!client) return
    try {
      await client.predict('/save_language', { language: local })
      setLanguage(local)
      setStatus('Language switched.')
    } catch (e) { setStatus(`Error: ${e.message}`) }
  }

  return (
    <Box sx={{ maxWidth: 360, display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box>
        <Typography variant="overline" sx={{ display: 'block', mb: 0.5 }}>Language</Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
          Applies to pipeline output labels, summaries, and audio reports.
        </Typography>
        <ToggleButtonGroup
          value={local}
          exclusive
          onChange={(_, v) => v && setLocal(v)}
          sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {LANGUAGES.map(lang => (
            <ToggleButton
              key={lang} value={lang}
              sx={{
                justifyContent: 'flex-start', gap: 1.5, px: 2, py: 1.25,
                borderRadius: '8px !important',
              }}>
              <Globe size={14} />
              {lang}
              {local === lang && (
                <Box sx={{ ml: 'auto', width: 8, height: 8, borderRadius: '50%', bgcolor: 'primary.main' }} />
              )}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Box>

      <Button
        variant="contained" color="primary"
        onClick={save}
        disabled={local === language}
        startIcon={<Save size={14} />}
        sx={{ alignSelf: 'flex-start' }}>
        Save Language
      </Button>

      {status && <Typography variant="caption" color="text.secondary">{status}</Typography>}
    </Box>
  )
}
