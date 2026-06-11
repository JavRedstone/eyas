import { useState, useEffect, useCallback, useRef } from 'react'
import { Client, prepare_files } from '@gradio/client'
import { AnimatePresence, motion } from 'framer-motion'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Splash from './components/Splash.jsx'
import Header from './components/Header.jsx'
import Sidebar from './components/Sidebar.jsx'
import AnalysisPanel from './components/AnalysisPanel.jsx'
import TabNav from './components/TabNav.jsx'
import EventTimeline from './components/tabs/EventTimeline.jsx'
import SummaryAlerts from './components/tabs/SummaryAlerts.jsx'
import AskFootage from './components/tabs/AskFootage.jsx'
import DetectionMetrics from './components/tabs/DetectionMetrics.jsx'
import AudioReport from './components/tabs/AudioReport.jsx'
import ClipLibrary from './components/tabs/ClipLibrary.jsx'
import SettingsTab from './components/tabs/SettingsTab.jsx'

const TABS = [
  { id: 'timeline',  label: 'Event Timeline',   icon: 'Activity'      },
  { id: 'alerts',    label: 'Summary & Alerts',  icon: 'AlertTriangle' },
  { id: 'qa',        label: 'Ask Footage',        icon: 'MessageSquare' },
  { id: 'metrics',   label: 'Detection Metrics',  icon: 'BarChart2'     },
  { id: 'audio',     label: 'Audio Report',       icon: 'Volume2'       },
  { id: 'library',   label: 'Clip Library',       icon: 'Film'          },
  { id: 'settings',  label: 'Settings',           icon: 'Settings'      },
]

export default function App() {
  const [client, setClient]                 = useState(null)
  const [splashItems, setSplashItems]       = useState([])
  const [splashPct, setSplashPct]           = useState(0)
  const [splashDone, setSplashDone]         = useState(false)
  const [activeTab, setActiveTab]           = useState('timeline')
  const [videoFile, setVideoFile]           = useState(null)
  const [videoRef, setVideoRef]             = useState(null)
  const [uploadStatus, setUploadStatus]     = useState('')
  const [analyzing, setAnalyzing]           = useState(false)
  const [statusMsg, setStatusMsg]           = useState('')
  const [pipelineSteps, setPipelineSteps]   = useState([])
  const [pipelineProgress, setPipelineProgress] = useState(0)
  const [annotatedVideo, setAnnotatedVideo] = useState(null)
  const [events, setEvents]                 = useState([])
  const [outputDir, setOutputDir]           = useState('')
  const [summary, setSummary]               = useState(null)
  const [chatHistory, setChatHistory]       = useState([])
  const [language, setLanguage]             = useState('English')
  const [samples, setSamples]               = useState([])
  const [videoPreviewSrc, setVideoPreviewSrc] = useState('')
  const [clipSrc, setClipSrc]               = useState(null)
  const previewUrlRef       = useRef('')
  const annotatedVideoElRef = useRef(null)
  const splitContainerRef   = useRef(null)
  const isDragging          = useRef(false)
  const [splitPct, setSplitPct] = useState(50)

  const seekAnnotatedVideo = useCallback((t) => {
    const el = annotatedVideoElRef.current
    if (!el) return
    el.currentTime = t
    if (el.paused) el.play().catch(() => {})
  }, [])

  const onDragHandleMouseDown = useCallback((e) => {
    e.preventDefault()
    isDragging.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    function onMove(e) {
      if (!isDragging.current || !splitContainerRef.current) return
      const rect = splitContainerRef.current.getBoundingClientRect()
      const pct  = ((e.clientX - rect.left) / rect.width) * 100
      setSplitPct(Math.max(25, Math.min(75, pct)))
    }
    function onUp() {
      isDragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }, [])

  function getVideoPath(fileRef) {
    if (!fileRef) return null
    if (typeof fileRef === 'string') {
      const prefix = '/gradio_api/file='
      return fileRef.startsWith(prefix) ? decodeURIComponent(fileRef.slice(prefix.length)) : fileRef
    }
    if (fileRef.path) return fileRef.path
    if (fileRef.url) {
      const prefix = '/gradio_api/file='
      return fileRef.url.startsWith(prefix) ? decodeURIComponent(fileRef.url.slice(prefix.length)) : null
    }
    return null
  }

  function getPreviewSrc(fileRef) {
    if (!fileRef) return null
    if (typeof fileRef === 'string') {
      if (fileRef.startsWith('http') || fileRef.startsWith('/gradio_api/file=')) return fileRef
      return `/gradio_api/file=${fileRef}`
    }
    if (fileRef.url) return fileRef.url
    if (fileRef.path) return `/gradio_api/file=${fileRef.path}`
    return null
  }

  function setPreviewSource(nextSrc) {
    if (previewUrlRef.current && previewUrlRef.current.startsWith('blob:')) URL.revokeObjectURL(previewUrlRef.current)
    previewUrlRef.current = nextSrc || ''
    setVideoPreviewSrc(nextSrc || '')
  }

  const pollSplash = useCallback(async (c) => {
    for (let i = 0; i < 60; i++) {
      try {
        const r = await c.predict('/poll_splash', {})
        const { states, done, progress_pct } = r.data[0]
        setSplashItems(states || [])
        setSplashPct(progress_pct ?? 0)
        if (done) { setSplashDone(true); return }
      } catch { return }
      await new Promise(res => setTimeout(res, 800))
    }
    setSplashDone(true)
  }, [])

  const loadSamples = useCallback(async (c) => {
    try {
      const r = await c.predict('/get_samples', {})
      setSamples(r.data[0] || [])
    } catch { return }
  }, [])

  useEffect(() => {
    Client.connect(window.location.origin)
      .then(c => { setClient(c); pollSplash(c); loadSamples(c) })
      .catch(() => null)
    return () => {
      if (previewUrlRef.current && previewUrlRef.current.startsWith('blob:')) URL.revokeObjectURL(previewUrlRef.current)
    }
  }, [loadSamples, pollSplash])

  const handleFileSelect = useCallback((file) => {
    setVideoFile(file)
    setVideoRef(null)
    setPreviewSource(URL.createObjectURL(file))
    setUploadStatus(`Ready: ${file.name}`)
  }, [])

  const handleLoadSample = useCallback(async (sampleName) => {
    if (!client || !sampleName) return
    try {
      setUploadStatus('Loading sample…')
      const r = await client.predict('/load_sample', { name: sampleName })
      setVideoRef(r.data[0])
      setVideoFile(null)
      setPreviewSource(getPreviewSrc(r.data[0]))
      setUploadStatus(`Sample: ${sampleName}`)
    } catch (e) { setUploadStatus(`Error: ${e.message}`) }
  }, [client])

  const handleAnalyze = useCallback(async () => {
    if (!client) return
    let gradioFile = getVideoPath(videoRef)
    if (!gradioFile && videoFile) {
      setStatusMsg('Uploading video…')
      try {
        const up = await client.upload(await prepare_files([videoFile]))
        gradioFile = getVideoPath(up[0])
        setVideoRef(up[0])
        setPreviewSource(getPreviewSrc(up[0]))
      } catch (e) { setStatusMsg(`Upload failed: ${e.message}`); return }
    }
    if (!gradioFile) { setStatusMsg('No video selected.'); return }
    setAnalyzing(true)
    setStatusMsg('Starting pipeline…')
    setPipelineSteps([])
    setPipelineProgress(0)
    setAnnotatedVideo(null)
    setEvents([])
    setSummary(null)
    try {
      const sub = client.submit('/run_pipeline', { video_path: gradioFile })
      for await (const msg of sub) {
        if (msg.type !== 'data') continue
        const u = msg.data[0]
        if (!u) continue
        if (u.status_msg || u.status) setStatusMsg(u.status_msg || u.status)
        if (u.pipeline_steps || u.steps) setPipelineSteps(u.pipeline_steps || u.steps)
        if (typeof u.progress_pct === 'number') setPipelineProgress(u.progress_pct)
        if (u.events?.length)        setEvents(u.events)
        if (u.output_dir)            setOutputDir(u.output_dir)
        if (u.annotated_video_path)  setAnnotatedVideo(u.annotated_video_path)
        if (u.type === 'final')    { setSummary(u); setPipelineProgress(100) }
      }
    } catch (e) { setStatusMsg(`Error: ${e.message}`) }
    finally      { setAnalyzing(false) }
  }, [client, videoFile, videoRef])

  const tabProps = { client, events, outputDir, summary, chatHistory, setChatHistory, language, setLanguage, onSeekVideo: seekAnnotatedVideo, setClipSrc }

  // Panel header utility
  const PanelHeader = ({ title, children }) => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
      <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'primary.main', flexShrink: 0 }} />
      <Typography variant="caption" fontWeight={600} sx={{ color: 'text.primary', letterSpacing: '0.03em' }}>
        {title}
      </Typography>
      {children}
    </Box>
  )

  return (
    <AnimatePresence mode="wait">
      {!splashDone ? (
        <Splash key="splash" items={splashItems} pct={splashPct} />
      ) : (
        <Box key="app" component={motion.div}
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}
          sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>

          <Header language={language} />

          {/* Resizable two-panel layout */}
          <Box ref={splitContainerRef}
            sx={{ display: 'flex', p: 2, flex: 1, minHeight: 0, overflow: 'hidden', gap: 0 }}>

            {/* Left panel */}
            <Box style={{ width: `${splitPct}%` }}
              sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, minHeight: 0, minWidth: 0 }}>
              <Sidebar
                samples={samples} videoFile={videoFile} videoRef={videoRef}
                uploadStatus={uploadStatus}
                onFileSelect={handleFileSelect} onLoadSample={handleLoadSample}
              />
              <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
                <PanelHeader title={clipSrc ? 'Event Clip' : annotatedVideo ? 'Annotated Video' : 'Preview'}>
                  {clipSrc && (
                    <Typography
                      component="button"
                      onClick={() => setClipSrc(null)}
                      sx={{ ml: 'auto', fontSize: '0.65rem', color: 'text.secondary', cursor: 'pointer', background: 'none', border: 'none', '&:hover': { color: 'text.primary' } }}>
                      ✕ close clip
                    </Typography>
                  )}
                </PanelHeader>
                <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#000', borderRadius: '0 0 11px 11px', overflow: 'hidden', minHeight: 0 }}>
                  {clipSrc ? (
                    <video key={clipSrc} src={clipSrc} controls autoPlay style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                  ) : annotatedVideo ? (
                    <video ref={annotatedVideoElRef}
                      src={annotatedVideo.startsWith('/gradio_api/file=') ? annotatedVideo : `/gradio_api/file=${annotatedVideo}`}
                      controls style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                  ) : videoPreviewSrc ? (
                    <video src={videoPreviewSrc} controls muted style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                  ) : (
                    <Box sx={{ textAlign: 'center', p: 4 }}>
                      <Typography sx={{ fontSize: '2rem', opacity: 0.2, mb: 1 }}>▶</Typography>
                      <Typography variant="caption" color="text.secondary">Load a sample or upload a video</Typography>
                    </Box>
                  )}
                </Box>
              </Paper>
            </Box>

            {/* Drag handle */}
            <Box sx={{ width: 16, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'col-resize', px: 0.5 }}
              onMouseDown={onDragHandleMouseDown}>
              <Box sx={{ width: 2, height: '100%', borderRadius: 9999, bgcolor: 'divider', transition: 'background-color 0.15s', '&:hover': { bgcolor: 'primary.dark' } }} />
            </Box>

            {/* Right panel */}
            <Box style={{ width: `${100 - splitPct}%` }}
              sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, minHeight: 0, minWidth: 0 }}>
              <AnalysisPanel
                analyzing={analyzing} statusMsg={statusMsg}
                pipelineSteps={pipelineSteps} pipelineProgress={pipelineProgress}
                onAnalyze={handleAnalyze}
              />
              <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                <TabNav tabs={TABS} activeTab={activeTab} setActiveTab={setActiveTab} />
                <Box sx={{ flex: 1, overflowY: 'auto', p: 2.5, minHeight: 0 }}>
                  <AnimatePresence mode="wait">
                    <Box key={activeTab} component={motion.div}
                      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.15 }}>
                      {activeTab === 'timeline' && <EventTimeline  {...tabProps} />}
                      {activeTab === 'alerts'   && <SummaryAlerts  {...tabProps} />}
                      {activeTab === 'qa'       && <AskFootage     {...tabProps} />}
                      {activeTab === 'metrics'  && <DetectionMetrics {...tabProps} />}
                      {activeTab === 'audio'    && <AudioReport    {...tabProps} />}
                      {activeTab === 'library'  && <ClipLibrary    {...tabProps} />}
                      {activeTab === 'settings' && <SettingsTab    {...tabProps} />}
                    </Box>
                  </AnimatePresence>
                </Box>
              </Paper>
            </Box>

          </Box>
        </Box>
      )}
    </AnimatePresence>
  )
}
