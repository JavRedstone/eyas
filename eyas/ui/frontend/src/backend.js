export const GRADIO_BACKEND_URL =
  import.meta.env.VITE_GRADIO_BACKEND_URL ||
  (import.meta.env.DEV ? 'http://127.0.0.1:7860' : window.location.origin)

export function backendUrl(value) {
  if (!value) return ''
  if (/^https?:\/\//i.test(value) || value.startsWith('blob:')) return value
  return new URL(value, `${GRADIO_BACKEND_URL}/`).toString()
}

export function gradioFileUrl(path) {
  if (!path) return ''
  if (path.startsWith('blob:')) return path
  if (/^https?:\/\//i.test(path)) {
    const url = new URL(path)
    if (!url.pathname.startsWith('/gradio_api/file=')) return path
    return backendUrl(`${url.pathname}${url.search}`)
  }
  if (path.startsWith('/gradio_api/file=')) return backendUrl(path)
  return backendUrl(`/gradio_api/file=${path}`)
}

export function resolveGradioFile(value) {
  if (!value) return ''
  if (typeof value === 'string') return gradioFileUrl(value)
  if (value.video) return resolveGradioFile(value.video)
  if (Array.isArray(value) && value.length > 0) return resolveGradioFile(value[0])
  if (value.url) return gradioFileUrl(value.url)
  if (value.path) return gradioFileUrl(value.path)
  return ''
}
