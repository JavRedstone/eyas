import { useRef } from 'react'
import { Upload } from 'lucide-react'
import { motion } from 'framer-motion'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'

export default function Sidebar({ samples, videoFile, videoRef, uploadStatus, onFileSelect, onLoadSample }) {
  const inputRef = useRef()
  const hasVideo = videoFile || videoRef

  function handleDrop(e) {
    e.preventDefault()
    const f = e.dataTransfer?.files?.[0]
    if (f && f.type.startsWith('video/')) onFileSelect(f)
  }

  function handleChange(e) {
    if (e.target.files[0]) onFileSelect(e.target.files[0])
  }

  return (
    <Paper>
      {/* Panel header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'primary.main' }} />
        <Typography variant="caption" fontWeight={600} sx={{ color: 'text.primary', letterSpacing: '0.03em' }}>Footage</Typography>
      </Box>

      <Box sx={{ p: 1.5, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {samples.length > 0 ? (
          <Box>
            <Typography variant="overline" sx={{ display: 'block', mb: 0.75, fontSize: '0.65rem' }}>Sample Clips</Typography>
            <FormControl size="small" fullWidth>
              <Select
                defaultValue=""
                onChange={e => onLoadSample(e.target.value)}
                displayEmpty
                sx={{ fontSize: '0.8rem' }}>
                <MenuItem value=""><em style={{ color: '#7a8ea8' }}>— Choose a sample —</em></MenuItem>
                {samples.map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
              </Select>
            </FormControl>
          </Box>
        ) : (
          <Typography variant="caption" color="text.secondary">No sample clips found.</Typography>
        )}

        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 0.75, fontSize: '0.65rem' }}>Upload Video</Typography>
          <Box
            component={motion.div}
            whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}
            onDragOver={e => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            sx={{
              border: '2px dashed',
              borderColor: hasVideo ? 'primary.dark' : 'divider',
              borderRadius: 2,
              p: 2,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: hasVideo ? 'rgba(247,208,70,0.04)' : 'transparent',
              transition: 'border-color 0.15s, background-color 0.15s',
              '&:hover': { borderColor: 'primary.dark', bgcolor: 'rgba(247,208,70,0.04)' },
            }}>
            <input ref={inputRef} type="file" accept="video/*" style={{ display: 'none' }} onChange={handleChange} />
            <Upload size={20} style={{ margin: '0 auto 8px', color: '#7a8ea8', display: 'block' }} />
            <Typography variant="caption" color="text.secondary">
              {videoFile ? videoFile.name : 'Drop video or click to upload'}
            </Typography>
          </Box>
        </Box>

        {uploadStatus && (
          <Typography variant="caption" color="text.secondary" noWrap>{uploadStatus}</Typography>
        )}
      </Box>
    </Paper>
  )
}
