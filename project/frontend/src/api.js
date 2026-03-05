const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('Backend unreachable')
  return res.json()
}

export async function fetchEvents(limit = 50) {
  const res = await fetch(`${API_BASE}/api/events?limit=${limit}`)
  if (!res.ok) throw new Error('Failed to fetch events')
  return res.json()
}

export async function analyzeVideo(file, scene = 'aggression') {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${API_BASE}/api/analyze?scene=${scene}`, {
    method: 'POST',
    body: fd,
  })
  if (!res.ok) throw new Error('Analysis failed')
  return res.json()
}

export async function clearEvents() {
  const res = await fetch(`${API_BASE}/api/events`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Clear failed')
  return res.json()
}
