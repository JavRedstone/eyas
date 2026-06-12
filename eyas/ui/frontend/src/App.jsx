import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { Client, prepare_files } from '@gradio/client'
import { AnimatePresence, motion } from 'framer-motion'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import { createEyasTheme } from './theme.js'
import { t } from './i18n.js'
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

function makeTabs(language) {
  return [
    { id: 'timeline',  label: t(language, 'tabs.timeline'), icon: 'Activity'      },
    { id: 'alerts',    label: t(language, 'tabs.alerts'),   icon: 'AlertTriangle' },
    { id: 'qa',        label: t(language, 'tabs.qa'),       icon: 'MessageSquare' },
    { id: 'metrics',   label: t(language, 'tabs.metrics'),  icon: 'BarChart2'     },
    { id: 'audio',     label: t(language, 'tabs.audio'),    icon: 'Volume2'       },
    { id: 'library',   label: t(language, 'tabs.library'),  icon: 'Film'          },
    { id: 'settings',  label: t(language, 'tabs.settings'), icon: 'Settings'      },
  ]
}

function parseFilenameZone(name) {
  const stem = name.replace(/\.[^.]+$/, '')
  const parts = stem.split('_')
  if (parts.length >= 3 && /^\d{8}$/.test(parts[0]) && /^\d{6}$/.test(parts[1]))
    return parts.slice(2).join('_')
  return ''
}

export default function App() {
  const [colorMode, setColorMode] = useState(() => {
    try { return localStorage.getItem('eyas-color-mode') || 'dark' } catch { return 'dark' }
  })
  const theme = useMemo(() => createEyasTheme(colorMode), [colorMode])
  function toggleColorMode() {
    setColorMode(m => {
      const next = m === 'dark' ? 'light' : 'dark'
      try { localStorage.setItem('eyas-color-mode', next) } catch {}
      return next
    })
  }

  const [client, setClient]                 = useState(null)
  const [splashItems, setSplashItems]       = useState([])
  const [splashPct, setSplashPct]           = useState(0)
  const [splashDone, setSplashDone]         = useState(false)
  const [activeTab, setActiveTab]           = useState('timeline')
  const [queue, setQueue]                   = useState([])
  const [analyzing, setAnalyzing]           = useState(false)
  const [stopping, setStopping]             = useState(false)
  const [processingItem, setProcessingItem] = useState(null)
  const [statusMsg, setStatusMsg]           = useState('')
  const [pipelineSteps, setPipelineSteps]   = useState([])
  const [pipelineProgress, setPipelineProgress] = useState(0)
  const [annotatedVideo, setAnnotatedVideo] = useState(null)
  const [events, setEvents]                 = useState([])
  const [outputDir, setOutputDir]           = useState('')
  const [summary, setSummary]               = useState(null)
  const [chatHistory, setChatHistory]       = useState([])
  const [language, setLanguage]             = useState('English')
  const tabs = useMemo(() => makeTabs(language), [language])
  const [samples, setSamples]               = useState([])
  const [videoPreviewSrc, setVideoPreviewSrc] = useState('')
  const [clipSrc, setClipSrc]               = useState(null)
  const [sessionRunCount, setSessionRunCount] = useState(0)
  const [exportingZip, setExportingZip]     = useState(false)
  const sessionEventsRef    = useRef([])
  const previewUrlRef       = useRef('')
  const annotatedVideoElRef = useRef(null)
  const splitContainerRef   = useRef(null)
  const isDragging          = useRef(false)
  const activeSubRef        = useRef(null)
  const stopRequestedRef    = useRef(false)
  const [splitPct, setSplitPct] = useState(50)

  const seekAnnotatedVideo = useCallback((time) => {
    const el = annotatedVideoElRef.current
    if (!el) return
    el.currentTime = time
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
    let langInitialized = false
    for (let i = 0; i < 60; i++) {
      try {
        const r = await c.predict('/poll_splash', {})
        const { states, done, progress_pct, language_label } = r.data[0]
        if (!langInitialized && language_label) {
          setLanguage(language_label)
          langInitialized = true
        }
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

  const handleToggleSelected = useCallback((id) => {
    setQueue(prev => prev.map(q => q.id === id ? { ...q, selected: !q.selected } : q))
  }, [])

  const handleSelectAll = useCallback((checked) => {
    setQueue(prev => prev.map(q => q.status === 'pending' ? { ...q, selected: checked } : q))
  }, [])

  const handleAddFilesToQueue = useCallback((files) => {
    const items = Array.from(files).map(file => ({
      id: Math.random().toString(36).slice(2),
      name: file.name,
      file,
      path: null,
      previewSrc: URL.createObjectURL(file),
      zone: parseFilenameZone(file.name),
      status: 'pending',
      selected: true,
      error: null,
    }))
    setQueue(prev => [...prev, ...items])
    if (items.length) setPreviewSource(items[0].previewSrc)
  }, [])

  const handleAddSampleToQueue = useCallback(async (sampleName) => {
    if (!client || !sampleName) return
    try {
      const r = await client.predict('/load_sample', { name: sampleName })
      const path = getVideoPath(r.data[0])
      const previewSrc = getPreviewSrc(r.data[0])
      setQueue(prev => [...prev, {
        id: Math.random().toString(36).slice(2),
        name: sampleName,
        file: null,
        path,
        previewSrc,
        zone: parseFilenameZone(sampleName),
        status: 'pending',
        selected: true,
        error: null,
      }])
      setPreviewSource(previewSrc)
    } catch (e) { setStatusMsg(`Error: ${e.message}`) }
  }, [client])

  const handleRemoveFromQueue = useCallback((id) => {
    setQueue(prev => {
      const item = prev.find(q => q.id === id)
      if (item?.file && item.previewSrc?.startsWith('blob:')) URL.revokeObjectURL(item.previewSrc)
      return prev.filter(q => q.id !== id)
    })
  }, [])

  const processItem = useCallback(async (item) => {
    let gradioPath = item.path
    if (!gradioPath && item.file) {
      setStatusMsg(t(language, 'app.uploading'))
      const up = await client.upload(await prepare_files([item.file]), client.config?.root ?? window.location.origin)
      const uploadedPath = getVideoPath(up[0])
      if (!uploadedPath) throw new Error('upload returned no path')
      gradioPath = uploadedPath
      setPreviewSource(getPreviewSrc(up[0]))
    }
    if (!gradioPath) throw new Error(t(language, 'app.no_video_selected'))

    const videoName = item.name
    setStatusMsg(t(language, 'app.starting_pipeline'))
    setPipelineSteps([])
    setPipelineProgress(0)
    setAnnotatedVideo(null)
    setSummary(null)

    const base = sessionEventsRef.current
    const sub = client.submit('/run_pipeline', { video_path: gradioPath })
    activeSubRef.current = sub
    for await (const msg of sub) {
      if (stopRequestedRef.current) break
      if (msg.type !== 'data') continue
      const u = msg.data[0]
      if (!u) continue
      if (u.status_msg || u.status) setStatusMsg(u.status_msg || u.status)
      if (u.pipeline_steps || u.steps) setPipelineSteps(u.pipeline_steps || u.steps)
      if (typeof u.progress_pct === 'number') setPipelineProgress(u.progress_pct)
      if (u.events?.length) {
        const tagged = u.events.map(e => ({ ...e, source_video: u.video_name ?? videoName }))
        setEvents([...base, ...tagged])
      }
      if (u.output_dir)           setOutputDir(u.output_dir)
      if (u.annotated_video_path) setAnnotatedVideo(u.annotated_video_path)
      if (u.type === 'final') {
        const tagged = (u.events || []).map(e => ({ ...e, source_video: u.video_name ?? videoName }))
        sessionEventsRef.current = [...base, ...tagged]
        setEvents(sessionEventsRef.current)
        setSessionRunCount(c => c + 1)
        setSummary(u)
        setPipelineProgress(100)
      }
    }
    activeSubRef.current = null
    if (stopRequestedRef.current) throw new Error('stopped')
  }, [client, language])

  const handleStop = useCallback(() => {
    if (stopping) return
    setStopping(true)
    stopRequestedRef.current = true
    activeSubRef.current?.cancel?.()
  }, [stopping])

  const handleAnalyzeAll = useCallback(async () => {
    if (!client || analyzing) return
    const pending = queue.filter(q => q.status === 'pending' && q.selected !== false)
    if (!pending.length) return
    stopRequestedRef.current = false
    setAnalyzing(true)
    for (const item of pending) {
      if (stopRequestedRef.current) break
      setProcessingItem({ name: item.name, zone: item.zone })
      setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'running' } : q))
      try {
        await processItem(item)
        setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'done' } : q))
      } catch (e) {
        if (stopRequestedRef.current) {
          setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'pending', error: null } : q))
          setStatusMsg('Stopped.')
          setPipelineSteps([])
          setPipelineProgress(0)
        } else {
          setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'error', error: e.message } : q))
          setStatusMsg(`Error: ${e.message}`)
        }
        break
      }
    }
    stopRequestedRef.current = false
    setStopping(false)
    setProcessingItem(null)
    setAnalyzing(false)
  }, [client, analyzing, queue, processItem])

  const handleSwitchLanguage = useCallback(async (lang) => {
    if (!client || lang === language) return
    try {
      await client.predict('/save_language', [lang])
      setLanguage(lang)
    } catch {}
  }, [client, language])

  const handleClearSession = useCallback(async () => {
    if (!window.confirm(t(language, 'session.clear_confirm'))) return
    try { await client?.predict('/clear_session', {}) } catch {}
    sessionEventsRef.current = []
    setEvents([])
    setSessionRunCount(0)
    setSummary(null)
    setOutputDir('')
    setAnnotatedVideo(null)
    setChatHistory([])
    setQueue(prev => prev.map(q => q.status !== 'pending' ? { ...q, status: 'pending', error: null } : q))
  }, [client, language])

  const handleExportZip = useCallback(async () => {
    if (!client) return
    setExportingZip(true)
    try {
      const r = await client.predict('/export_session_zip', {})
      const file = r.data[0]
      const filePath = file?.path ?? file?.url ?? file
      if (filePath) {
        const url = String(filePath).startsWith('/') ? filePath : `/gradio_api/file=${filePath}`
        const a = document.createElement('a')
        a.href = url
        a.download = `eyas_session_${new Date().toISOString().slice(0, 10)}.zip`
        a.click()
      }
    } catch (e) { console.error('Export failed', e) }
    finally { setExportingZip(false) }
  }, [client])

  const queuePending = queue.filter(q => q.status === 'pending' && q.selected !== false).length
  const queueDone    = queue.filter(q => q.status === 'done' || q.status === 'error').length
  const allPendingSelected = queue.filter(q => q.status === 'pending').every(q => q.selected !== false)
  const somePendingSelected = queue.some(q => q.status === 'pending' && q.selected !== false)

  const tabProps = { client, events, outputDir, summary, chatHistory, setChatHistory, language, setLanguage, onSeekVideo: seekAnnotatedVideo, setClipSrc }

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
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Header language={language} colorMode={colorMode} onToggleColorMode={toggleColorMode} onSwitchLanguage={handleSwitchLanguage} />
        <AnimatePresence mode="wait">
          {!splashDone ? (
            <Splash key="splash" items={splashItems} pct={splashPct} language={language} colorMode={colorMode} />
          ) : (
            <Box key="app" component={motion.div}
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}
              sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

              <Box ref={splitContainerRef}
                sx={{ display: 'flex', p: 2, flex: 1, minHeight: 0, overflow: 'hidden', gap: 0 }}>

                {/* Left panel */}
                <Box style={{ width: `${splitPct}%` }}
                  sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, minHeight: 0, minWidth: 0 }}>
                  <Sidebar
                    samples={samples} queue={queue} language={language}
                    onAddFiles={handleAddFilesToQueue} onAddSample={handleAddSampleToQueue}
                    onRemoveItem={handleRemoveFromQueue}
                    onToggleSelected={handleToggleSelected}
                    onSelectAll={handleSelectAll}
                    allPendingSelected={allPendingSelected}
                    somePendingSelected={somePendingSelected}
                    sessionEventCount={events.length} sessionRunCount={sessionRunCount}
                    onClearSession={handleClearSession} onExportZip={handleExportZip}
                    exportingZip={exportingZip}
                  />
                  <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
                    <PanelHeader title={clipSrc ? t(language, 'panel.event_clip') : annotatedVideo ? t(language, 'panel.annotated') : t(language, 'panel.preview')}>
                      {clipSrc && (
                        <Typography
                          component="button"
                          onClick={() => setClipSrc(null)}
                          sx={{ ml: 'auto', fontSize: '0.65rem', color: 'text.secondary', cursor: 'pointer', background: 'none', border: 'none', '&:hover': { color: 'text.primary' } }}>
                          {t(language, 'app.close_clip')}
                        </Typography>
                      )}
                    </PanelHeader>
                    <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: (clipSrc || annotatedVideo || videoPreviewSrc) ? '#000' : 'background.default', borderRadius: '0 0 11px 11px', overflow: 'hidden', minHeight: 0 }}>
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
                          <Typography variant="caption" color="text.secondary">{t(language, 'app.no_video')}</Typography>
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
                    analyzing={analyzing} stopping={stopping} statusMsg={statusMsg}
                    pipelineSteps={pipelineSteps} pipelineProgress={pipelineProgress}
                    onAnalyzeAll={handleAnalyzeAll} onStop={handleStop}
                    queuePending={queuePending} queueDone={queueDone} queueTotal={queue.length}
                    processingItem={processingItem}
                    language={language}
                  />
                  <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                    <TabNav tabs={tabs} activeTab={activeTab} setActiveTab={setActiveTab} />
                    <Box sx={{ flex: 1, overflowY: 'auto', p: 2.5, minHeight: 0 }}>
                      <Box sx={{ display: activeTab === 'timeline' ? 'block' : 'none' }}><EventTimeline   {...tabProps} /></Box>
                      <Box sx={{ display: activeTab === 'alerts'   ? 'block' : 'none' }}><SummaryAlerts   {...tabProps} /></Box>
                      <Box sx={{ display: activeTab === 'qa'       ? 'block' : 'none' }}><AskFootage      {...tabProps} /></Box>
                      <Box sx={{ display: activeTab === 'metrics'  ? 'block' : 'none' }}><DetectionMetrics {...tabProps} /></Box>
                      <Box sx={{ display: activeTab === 'audio'    ? 'block' : 'none' }}><AudioReport     {...tabProps} /></Box>
                      <Box sx={{ display: activeTab === 'library'  ? 'block' : 'none' }}><ClipLibrary     {...tabProps} /></Box>
                      <Box sx={{ display: activeTab === 'settings' ? 'block' : 'none' }}><SettingsTab     {...tabProps} /></Box>
                    </Box>
                  </Paper>
                </Box>

              </Box>
            </Box>
          )}
        </AnimatePresence>
      </Box>
    </ThemeProvider>
  )
}
