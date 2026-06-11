import { useState, useRef, useEffect } from 'react'
import { Send, Trash2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import IconButton from '@mui/material/IconButton'
import Chip from '@mui/material/Chip'

export default function AskFootage({ client, events, chatHistory, setChatHistory }) {
  const [query, setQuery]   = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef()
  const suggestions = [
    'What activity was detected?',
    'Were any suspicious events found?',
    'Which zones had the most activity?',
    'Summarize the key events',
  ]

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [chatHistory])

  async function ask() {
    const q = query.trim()
    if (!q || !client || loading) return
    setQuery('')
    const newHistory = [...chatHistory, { role: 'user', text: q }]
    setChatHistory(newHistory)
    setLoading(true)
    try {
      const r = await client.predict('/ask_footage', {
        message: q,
        history: newHistory.map(h => [h.role === 'user' ? h.text : null, h.role === 'assistant' ? h.text : null]),
        events,
      })
      const replyHistory = r.data[0] || []
      const answer = extractAssistantReply(replyHistory)
      setChatHistory(h => [...h, { role: 'assistant', text: answer || 'No response.' }])
    } catch (e) {
      setChatHistory(h => [...h, { role: 'assistant', text: `Error: ${e.message}` }])
    } finally { setLoading(false) }
  }

  function handleKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask() } }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 420 }}>
      <Typography variant="overline" sx={{ display: 'block', mb: 1.5 }}>Ask a Question About the Footage</Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5 }}>
        Try: "Were there any unusual events?" · "Which zone had the most activity?"
      </Typography>

      {/* Suggestion chips */}
      <Box sx={{ mb: 1.5, display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
        {suggestions.map(suggestion => (
          <Chip
            key={suggestion}
            label={suggestion}
            size="small"
            variant="outlined"
            disabled={loading}
            onClick={() => setQuery(suggestion)}
            sx={{
              borderColor: 'divider',
              bgcolor: 'rgba(20,45,79,0.5)',
              color: 'text.primary',
              cursor: 'pointer',
              '&:hover': { borderColor: 'rgba(247,208,70,0.4)', bgcolor: 'rgba(247,208,70,0.05)' },
            }}
          />
        ))}
      </Box>

      {/* Chat area */}
      <Box sx={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 1.5, mb: 1.5, minHeight: 0 }}>
        {chatHistory.length === 0 && (
          <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center', mt: 4, display: 'block' }}>
            No conversation yet. Run a pipeline first, then ask questions.
          </Typography>
        )}
        <AnimatePresence initial={false}>
          {chatHistory.map((msg, i) => (
            <Box key={i} component={motion.div}
              initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
              sx={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <Paper sx={{
                maxWidth: '75%', px: 1.5, py: 1, borderRadius: 3,
                bgcolor: msg.role === 'user' ? 'primary.main' : 'background.paper',
                color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                borderBottomRightRadius: msg.role === 'user' ? 4 : undefined,
                borderBottomLeftRadius: msg.role === 'assistant' ? 4 : undefined,
              }}>
                <Typography variant="caption" sx={{ lineHeight: 1.6 }}>{msg.text}</Typography>
              </Paper>
            </Box>
          ))}
        </AnimatePresence>
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
            <Paper sx={{ px: 1.5, py: 1, borderRadius: 3, borderBottomLeftRadius: 4 }}>
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                {[0, 1, 2].map(i => (
                  <Box key={i} component={motion.div}
                    sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'text.secondary' }}
                    animate={{ y: [0, -4, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }} />
                ))}
              </Box>
            </Paper>
          </Box>
        )}
        <div ref={bottomRef} />
      </Box>

      {/* Input row */}
      <Box sx={{ display: 'flex', gap: 1, flexShrink: 0 }}>
        <TextField
          size="small"
          fullWidth
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask a question about the footage…"
          variant="outlined"
          sx={{ '& input': { fontSize: '0.8rem' } }}
        />
        <IconButton
          onClick={ask}
          disabled={!query.trim() || loading}
          color="primary"
          sx={{ bgcolor: 'primary.main', color: 'primary.contrastText', borderRadius: 1.5, '&:hover': { bgcolor: 'primary.dark' }, '&.Mui-disabled': { opacity: 0.4, bgcolor: 'primary.main', color: 'primary.contrastText' } }}>
          <Send size={16} />
        </IconButton>
        {chatHistory.length > 0 && (
          <IconButton onClick={() => setChatHistory([])} sx={{ borderRadius: 1.5 }}>
            <Trash2 size={16} />
          </IconButton>
        )}
      </Box>
    </Box>
  )
}

function extractAssistantReply(replyHistory) {
  if (!Array.isArray(replyHistory) || replyHistory.length === 0) return ''
  for (let i = replyHistory.length - 1; i >= 0; i--) {
    const msg = replyHistory[i]
    if (!msg || msg.role !== 'assistant') continue
    return msg.text ?? msg.content ?? ''
  }
  const last = replyHistory[replyHistory.length - 1]
  return last?.text ?? last?.content ?? ''
}
