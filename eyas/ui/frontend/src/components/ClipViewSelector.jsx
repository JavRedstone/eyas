import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { CheckCircle, XCircle, Loader2, Layers } from 'lucide-react'
import { t } from '../i18n.js'
import { displayZone } from '../display.js'

const STATUS_COLOR = {
  done:    '#34D399',
  error:   '#F87171',
  running: '#f7d046',
}

function StatusIcon({ status }) {
  const style = { flexShrink: 0 }
  if (status === 'running') return <Loader2 size={10} style={{ ...style, color: '#f7d046', animation: 'spin 1s linear infinite' }} />
  if (status === 'done')    return <CheckCircle size={10} style={{ ...style, color: '#34D399' }} />
  if (status === 'error')   return <XCircle size={10} style={{ ...style, color: '#F87171' }} />
  return null
}

function ViewChip({ label, icon, selected, color, borderColor, onClick }) {
  return (
    <Box
      component="button"
      onClick={onClick}
      sx={{
        display: 'flex', alignItems: 'center', gap: 0.5,
        px: 1, py: 0.375,
        border: '1px solid',
        borderColor: selected ? (borderColor || 'rgba(247,208,70,0.5)') : 'divider',
        borderRadius: 1.5,
        background: selected ? 'rgba(247,208,70,0.08)' : 'transparent',
        color: selected ? (color || 'primary.main') : 'text.secondary',
        cursor: 'pointer',
        flexShrink: 0,
        transition: 'all 0.12s',
        '&:hover': {
          borderColor: borderColor || 'rgba(247,208,70,0.35)',
          background: 'rgba(247,208,70,0.05)',
          color: color || 'primary.main',
        },
      }}
    >
      {icon}
      <Typography variant="caption" sx={{ fontSize: '0.65rem', fontFamily: 'monospace', lineHeight: 1, color: 'inherit', whiteSpace: 'nowrap' }}>
        {label}
      </Typography>
    </Box>
  )
}

export default function ClipViewSelector({ queue = [], viewClipId, onChange, language = 'English', zoneKoCache = {} }) {
  const nonPending = queue.filter(q => q.status !== 'pending')
  if (!nonPending.length) return null

  return (
    <Box
      sx={{
        display: 'flex', alignItems: 'center', gap: 0.5,
        px: 1.5, py: 0.75,
        borderBottom: '1px solid', borderColor: 'divider',
        overflowX: 'auto',
        '&::-webkit-scrollbar': { height: 3 },
        '&::-webkit-scrollbar-thumb': { background: 'rgba(247,208,70,0.2)', borderRadius: 2 },
      }}
    >
      <ViewChip
        label={t(language, 'clip_view.all')}
        icon={<Layers size={10} style={{ flexShrink: 0 }} />}
        selected={viewClipId === null}
        onClick={() => onChange(null)}
      />

      <Box sx={{ width: '1px', height: 14, bgcolor: 'divider', flexShrink: 0, mx: 0.25 }} />

      {nonPending.map(item => {
        const isSelected = viewClipId === item.id
        const label = item.zone
          ? displayZone(item.zone, language, zoneKoCache)
          : item.name.replace(/\.[^.]+$/, '').slice(-18)
        const statusColor = STATUS_COLOR[item.status]
        return (
          <ViewChip
            key={item.id}
            label={label}
            icon={<StatusIcon status={item.status} />}
            selected={isSelected}
            color={isSelected ? (statusColor || 'primary.main') : undefined}
            borderColor={isSelected ? `${statusColor}66` : undefined}
            onClick={() => onChange(item.id)}
          />
        )
      })}
    </Box>
  )
}
