import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import * as Icons from 'lucide-react'

export default function SidebarTabs({ tabs, activeTab, setActiveTab }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <Box
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
      sx={{
        width: expanded ? 164 : 44,
        transition: 'width 0.18s ease',
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid',
        borderColor: 'divider',
        overflow: 'hidden',
        bgcolor: 'background.paper',
        zIndex: 1,
        pt: 0.5,
      }}>
      {tabs.map(tab => {
        const Icon = Icons[tab.icon] || Icons.Circle
        const isActive = activeTab === tab.id
        return (
          <Box
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1.25,
              pl: 1.5,
              pr: 1,
              py: 1.1,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              color: isActive ? 'primary.main' : 'text.secondary',
              bgcolor: isActive ? 'rgba(247,208,70,0.07)' : 'transparent',
              borderLeft: '2px solid',
              borderColor: isActive ? 'primary.main' : 'transparent',
              transition: 'background-color 0.12s, color 0.12s',
              '&:hover': {
                bgcolor: isActive ? 'rgba(247,208,70,0.1)' : 'rgba(255,255,255,0.04)',
                color: isActive ? 'primary.main' : 'text.primary',
              },
            }}>
            <Icon size={15} style={{ flexShrink: 0 }} />
            <Typography
              variant="caption"
              fontWeight={isActive ? 600 : 400}
              sx={{
                fontSize: '0.7rem',
                opacity: expanded ? 1 : 0,
                transition: 'opacity 0.12s ease',
                letterSpacing: '0.02em',
              }}>
              {tab.label}
            </Typography>
          </Box>
        )
      })}
    </Box>
  )
}
