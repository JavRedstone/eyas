import { motion } from 'framer-motion'
import * as Icons from 'lucide-react'

export default function TabNav({ tabs, activeTab, setActiveTab }) {
  return (
    <div className="flex items-center gap-1 px-3 pt-3 pb-0 border-b border-border overflow-x-auto">
      {tabs.map(tab => {
        const Icon = Icons[tab.icon] || Icons.Circle
        const active = activeTab === tab.id
        return (
          <button key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`relative flex items-center gap-1.5 px-3 py-2 rounded-t-lg text-xs font-medium
              whitespace-nowrap transition-colors duration-150
              ${active ? 'text-text' : 'text-muted hover:text-text/80'}`}>
            <Icon size={13} />
            {tab.label}
            {active && (
              <motion.div layoutId="tab-underline"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-full"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }} />
            )}
          </button>
        )
      })}
    </div>
  )
}
