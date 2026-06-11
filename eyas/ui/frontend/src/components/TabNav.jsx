import Tabs from '@mui/material/Tabs'
import Tab from '@mui/material/Tab'
import Box from '@mui/material/Box'
import * as Icons from 'lucide-react'

export default function TabNav({ tabs, activeTab, setActiveTab }) {
  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 1 }}>
      <Tabs
        value={activeTab}
        onChange={(_, v) => setActiveTab(v)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ minHeight: 44 }}>
        {tabs.map(tab => {
          const Icon = Icons[tab.icon] || Icons.Circle
          return (
            <Tab
              key={tab.id}
              value={tab.id}
              label={tab.label}
              icon={<Icon size={13} />}
              iconPosition="start"
              sx={{ minHeight: 44, gap: 0.75, px: 1.5 }}
            />
          )
        })}
      </Tabs>
    </Box>
  )
}
