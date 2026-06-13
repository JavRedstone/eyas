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
import SidebarTabs from './components/SidebarTabs.jsx'
import EventTimeline from './components/tabs/EventTimeline.jsx'
import SummaryAlerts from './components/tabs/SummaryAlerts.jsx'
import AskFootage from './components/tabs/AskFootage.jsx'
import DetectionMetrics from './components/tabs/DetectionMetrics.jsx'
import AudioReport from './components/tabs/AudioReport.jsx'
import ClipLibrary from './components/tabs/ClipLibrary.jsx'
import ClipViewSelector from './components/ClipViewSelector.jsx'

function makeTabs(language) {
  return [
    { id: 'timeline',  label: t(language, 'tabs.timeline'), icon: 'Activity'      },
    { id: 'alerts',    label: t(language, 'tabs.alerts'),   icon: 'AlertTriangle' },
    { id: 'qa',        label: t(language, 'tabs.qa'),       icon: 'MessageSquare' },
    { id: 'metrics',   label: t(language, 'tabs.metrics'),  icon: 'BarChart2'     },
    { id: 'audio',     label: t(language, 'tabs.audio'),    icon: 'Volume2'       },
    { id: 'library',   label: t(language, 'tabs.library'),  icon: 'Film'          },
  ]
}

function parseFilenameZone(name) {
  const stem = name.replace(/\.[^.]+$/, '')
  const parts = stem.split('_')
  if (parts.length >= 3 && /^\d{8}$/.test(parts[0]) && /^\d{6}$/.test(parts[1]))
    return parts.slice(2).join('_')
  return ''
}

function normalizeVideoKey(name) {
  return (name || '').replace(/\.[^.]+$/, '').toLowerCase()
}

function eventBelongsToClip(event, clip) {
  if (!clip) return true
  if (event.source_clip_id === clip.id) return true
  return normalizeVideoKey(event.source_video) === normalizeVideoKey(clip.name)
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
  const [viewClipId, setViewClipId]         = useState(null)
  const [previewQueueId, setPreviewQueueId] = useState(null)

  const [topColPct, setTopColPct] = useState(40)

  const topRowRef  = useRef(null)

  const sessionEventsRef    = useRef([])
  const previewUrlRef       = useRef('')
  const annotatedVideoElRef = useRef(null)
  const activeSubRef        = useRef(null)
  const stopRequestedRef    = useRef(false)

  const makeDragHandler = useCallback((containerRef, setter, direction, lo = 20, hi = 80) =>
    (e) => {
      e.preventDefault()
      document.body.style.cursor = direction === 'col' ? 'col-resize' : 'row-resize'
      document.body.style.userSelect = 'none'
      const onMove = (ev) => {
        if (!containerRef.current) return
        const rect = containerRef.current.getBoundingClientRect()
        const pct = direction === 'col'
          ? ((ev.clientX - rect.left)  / rect.width)  * 100
          : ((ev.clientY - rect.top)   / rect.height) * 100
        setter(Math.max(lo, Math.min(hi, pct)))
      }
      const onUp = () => {
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
        window.removeEventListener('mousemove', onMove)
        window.removeEventListener('mouseup', onUp)
      }
      window.addEventListener('mousemove', onMove)
      window.addEventListener('mouseup', onUp)
    }, [])

  const onTopColDrag = useMemo(() => makeDragHandler(topRowRef, setTopColPct, 'col', 25, 70), [makeDragHandler])

  const seekAnnotatedVideo = useCallback((time) => {
    const el = annotatedVideoElRef.current
    if (!el) return
    el.currentTime = time
    if (el.paused) el.play().catch(() => {})
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
    if (items.length) {
      setPreviewSource(items[0].previewSrc)
      setPreviewQueueId(items[0].id)
    }
  }, [])

  const handleAddSampleToQueue = useCallback(async (sampleName) => {
    if (!client || !sampleName) return
    try {
      const r = await client.predict('/load_sample', { name: sampleName })
      const path = getVideoPath(r.data[0])
      const previewSrc = getPreviewSrc(r.data[0])
      const newId = Math.random().toString(36).slice(2)
      setQueue(prev => [...prev, {
        id: newId,
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
      setPreviewQueueId(newId)
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
    let itemResults = null
    for await (const msg of sub) {
      if (stopRequestedRef.current) break
      if (msg.type !== 'data') continue
      const u = msg.data[0]
      if (!u) continue
      if (u.status_msg || u.status) setStatusMsg(u.status_msg || u.status)
      if (u.pipeline_steps || u.steps) setPipelineSteps(u.pipeline_steps || u.steps)
      if (typeof u.progress_pct === 'number') setPipelineProgress(u.progress_pct)
      if (u.events?.length) {
        const tagged = u.events.map((e, i) => ({
          ...e,
          source_video: videoName,
          source_clip_id: item.id,
          source_event_index: i,
          ...(u.output_dir ? { source_output_dir: u.output_dir } : {}),
        }))
        setEvents([...base, ...tagged])
      }
      if (u.output_dir)           setOutputDir(u.output_dir)
      if (u.annotated_video_path) setAnnotatedVideo(u.annotated_video_path)
      if (u.type === 'final') {
        const tagged = (u.events || []).map((e, i) => ({
          ...e,
          source_video: videoName,
          source_clip_id: item.id,
          source_event_index: i,
          ...(u.output_dir ? { source_output_dir: u.output_dir } : {}),
        }))
        sessionEventsRef.current = [...base, ...tagged]
        setEvents(sessionEventsRef.current)
        setSessionRunCount(c => c + 1)
        setSummary(u)
        setPipelineProgress(100)
        itemResults = {
          summary: u,
          annotatedVideo: u.annotated_video_path || null,
          outputDir: u.output_dir || '',
        }
      }
    }
    activeSubRef.current = null
    if (stopRequestedRef.current) throw new Error('stopped')
    return itemResults
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
        const results = await processItem(item)
        setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'done', results } : q))
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
    setViewClipId(null)
    setOutputDir('')
    setAnnotatedVideo(null)
    setChatHistory([])
    setPreviewQueueId(null)
    setQueue(prev => prev.map(q => q.status !== 'pending' ? { ...q, status: 'pending', error: null } : q))
  }, [client, language])

  const handleSelectPreview = useCallback((item) => {
    if (item.previewSrc) {
      setPreviewSource(item.previewSrc)
      setPreviewQueueId(item.id)
      setClipSrc(null)
    }
  }, [])

  const handleExportZip = useCallback(async () => {
    if (!client) return
    setExportingZip(true)
    try {
      const r = await client.predict('/export_session_zip', {})
      console.log('[export] raw response:', r)
      console.log('[export] r.data[0]:', r.data[0])
      const payload = r.data[0]
      const { data } = payload
      console.log('[export] base64 data length:', data?.length, 'first 40:', data?.slice(0, 40))
      const bytes = Uint8Array.from(atob(data), c => c.charCodeAt(0))
      const blob = new Blob([bytes], { type: 'application/zip' })
      const url = URL.createObjectURL(blob)
      console.log('[export] blob url:', url, 'size:', blob.size)
      const a = document.createElement('a')
      a.href = url
      a.download = `eyas_session_${new Date().toISOString().slice(0, 10)}.zip`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) { console.error('[export] failed:', e) }
    finally { setExportingZip(false) }
  }, [client])

  const queuePending = queue.filter(q => q.status === 'pending' && q.selected !== false).length
  const queueDone    = queue.filter(q => q.status === 'done' || q.status === 'error').length
  const allPendingSelected = queue.filter(q => q.status === 'pending').every(q => q.selected !== false)
  const somePendingSelected = queue.some(q => q.status === 'pending' && q.selected !== false)

  const viewClip           = viewClipId ? queue.find(q => q.id === viewClipId) : null
  const viewEvents         = viewClipId ? events.filter(e => eventBelongsToClip(e, viewClip)) : events
  const viewSummary        = viewClipId ? (viewClip?.results?.summary ?? null) : summary
  const viewAnnotatedVideo = viewClipId ? (viewClip?.results?.annotatedVideo ?? null) : annotatedVideo
  const viewOutputDir      = viewClipId ? (viewClip?.results?.outputDir ?? '') : outputDir

  const tabProps = {
    client,
    events: viewEvents,
    outputDir: viewOutputDir,
    summary: viewSummary,
    chatHistory, setChatHistory,
    language, setLanguage,
    onSeekVideo: seekAnnotatedVideo,
    setClipSrc,
    annotatedVideo: viewAnnotatedVideo,
    annotatedVideoRef: annotatedVideoElRef,
  }

  const PanelHeader = ({ title, children }) => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 1.25, borderBottom: '1px solid', borderColor: 'divider', flexShrink: 0 }}>
      <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'primary.main', flexShrink: 0 }} />
      <Typography variant="caption" fontWeight={600} sx={{ color: 'text.primary', letterSpacing: '0.03em' }}>
        {title}
      </Typography>
      {children}
    </Box>
  )

  const ColHandle = ({ onMouseDown }) => (
    <Box sx={{ width: 14, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'col-resize', px: 0.25 }}
      onMouseDown={onMouseDown}>
      <Box sx={{ width: 2, height: '60%', minHeight: 40, borderRadius: 9999, bgcolor: 'divider', transition: 'background-color 0.15s', '&:hover': { bgcolor: 'primary.dark' } }} />
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
              sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, p: 2, gap: 1.5, overflow: 'hidden' }}>

              {/* ── TOP ROW: Queue/Analysis + Footage Preview ─────────────────── */}
              <Box ref={topRowRef}
                sx={{ flex: '0 0 42%', display: 'flex', minHeight: 0, gap: 0 }}>

                {/* Top-left: queue sidebar + analysis panel */}
                <Box style={{ flex: topColPct }}
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
                  <AnalysisPanel
                    analyzing={analyzing} stopping={stopping} statusMsg={statusMsg}
                    pipelineSteps={pipelineSteps} pipelineProgress={pipelineProgress}
                    onAnalyzeAll={handleAnalyzeAll} onStop={handleStop}
                    queuePending={queuePending} queueDone={queueDone} queueTotal={queue.length}
                    processingItem={processingItem}
                    language={language}
                  />
                </Box>

                <ColHandle onMouseDown={onTopColDrag} />

                {/* Top-right: raw footage / event clip preview */}
                <Box style={{ flex: 100 - topColPct }}
                  sx={{ display: 'flex', flexDirection: 'column', minHeight: 0, minWidth: 0 }}>
                  <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
                    <PanelHeader title={clipSrc ? t(language, 'panel.event_clip') : t(language, 'panel.preview')}>
                      {clipSrc && (
                        <Typography
                          component="button"
                          onClick={() => setClipSrc(null)}
                          sx={{ ml: 'auto', fontSize: '0.65rem', color: 'text.secondary', cursor: 'pointer', background: 'none', border: 'none', '&:hover': { color: 'text.primary' } }}>
                          {t(language, 'app.close_clip')}
                        </Typography>
                      )}
                    </PanelHeader>

                    {/* Source selector strip */}
                    {queue.length > 0 && (
                      <Box sx={{ flexShrink: 0, display: 'flex', gap: 0.5, px: 1.5, py: 0.75, borderBottom: '1px solid', borderColor: 'divider', overflowX: 'auto', '&::-webkit-scrollbar': { display: 'none' } }}>
                        {queue.map(item => {
                          const isActive = !clipSrc && previewQueueId === item.id
                          return (
                            <Box
                              key={item.id}
                              onClick={() => handleSelectPreview(item)}
                              sx={{
                                flexShrink: 0,
                                px: 1, py: 0.25,
                                borderRadius: 1,
                                cursor: 'pointer',
                                border: '1px solid',
                                borderColor: isActive ? 'primary.main' : 'divider',
                                bgcolor: isActive ? 'rgba(247,208,70,0.1)' : 'transparent',
                                color: isActive ? 'primary.main' : 'text.secondary',
                                fontSize: '0.65rem',
                                fontFamily: 'monospace',
                                whiteSpace: 'nowrap',
                                maxWidth: isActive ? 'none' : 96,
                                overflow: isActive ? 'visible' : 'hidden',
                                textOverflow: isActive ? 'clip' : 'ellipsis',
                                transition: 'max-width 0.18s ease, background-color 0.12s, color 0.12s',
                                '&:hover': { borderColor: 'primary.main', color: 'text.primary' },
                              }}>
                              {item.name}
                            </Box>
                          )
                        })}
                      </Box>
                    )}

                    <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: (clipSrc || videoPreviewSrc) ? '#000' : 'background.default', borderRadius: '0 0 11px 11px', overflow: 'hidden', minHeight: 0 }}>
                      {clipSrc ? (
                        <video key={clipSrc} src={clipSrc} controls autoPlay style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
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
              </Box>

              {/* ── BOTTOM ROW: icon sidebar + per-tab layouts ────────────────── */}
              <Box sx={{ flex: 1, display: 'flex', minHeight: 0, gap: 0 }}>

                <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
                  <ClipViewSelector queue={queue} viewClipId={viewClipId} onChange={setViewClipId} />

                  <Box sx={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
                    <SidebarTabs tabs={tabs} activeTab={activeTab} setActiveTab={setActiveTab} />

                    {/* EventTimeline: owns its own flex layout */}
                    <Box sx={{ display: activeTab === 'timeline' ? 'flex' : 'none', flex: 1, flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
                      <EventTimeline {...tabProps} />
                    </Box>

                    {/* AskFootage: flex-height chat */}
                    <Box sx={{ display: activeTab === 'qa' ? 'flex' : 'none', flex: 1, flexDirection: 'column', minHeight: 0, overflow: 'hidden', p: 2.5 }}>
                      <AskFootage {...tabProps} />
                    </Box>

                    {/* Scrollable tabs */}
                    <Box sx={{ display: activeTab === 'alerts'  ? 'block' : 'none', flex: 1, overflowY: 'auto', p: 2.5 }}>
                      <SummaryAlerts {...tabProps} />
                    </Box>
                    <Box sx={{ display: activeTab === 'metrics' ? 'block' : 'none', flex: 1, overflowY: 'auto', p: 2.5 }}>
                      <DetectionMetrics {...tabProps} />
                    </Box>
                    <Box sx={{ display: activeTab === 'audio'   ? 'block' : 'none', flex: 1, overflowY: 'auto', p: 2.5 }}>
                      <AudioReport {...tabProps} />
                    </Box>
                    <Box sx={{ display: activeTab === 'library' ? 'flex' : 'none', flex: 1, flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
                      <ClipLibrary {...tabProps} />
                    </Box>
                  </Box>
                </Paper>
              </Box>

            </Box>
          )}
        </AnimatePresence>
      </Box>
    </ThemeProvider>
  )
}
