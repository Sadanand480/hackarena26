import { useEffect, useState, useRef, useCallback } from 'react'
import { fetchEvents, analyzeVideo, clearEvents, fetchHealth } from './api'

const scoreColor = (s) => {
  if (s >= 80) return '#ff2d55'
  if (s >= 60) return '#ff9f0a'
  if (s >= 40) return '#ffd60a'
  return '#30d158'
}
const scoreBg = (s) => {
  if (s >= 80) return 'rgba(255,45,85,0.12)'
  if (s >= 60) return 'rgba(255,159,10,0.12)'
  if (s >= 40) return 'rgba(255,214,10,0.12)'
  return 'rgba(48,209,88,0.12)'
}

function ThreatGauge({ score }) {
  const r = 54, cx = 70, cy = 70
  const circumference = 2 * Math.PI * r
  const arcLen = (270 / 360) * circumference
  const dashoffset = arcLen - (score / 100) * arcLen
  const col = scoreColor(score)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div style={{ position: 'relative', width: 140, height: 140 }}>
        <svg width="140" height="140" style={{ transform: 'rotate(-135deg)', transformOrigin: '70px 70px' }}>
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1c2030" strokeWidth="10"
            strokeDasharray={`${arcLen} ${circumference - arcLen}`} strokeLinecap="round" />
          <circle cx={cx} cy={cy} r={r} fill="none" stroke={col} strokeWidth="10"
            strokeDasharray={`${arcLen} ${circumference - arcLen}`}
            strokeDashoffset={dashoffset} strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease, stroke 0.4s' }} />
        </svg>
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 30, fontWeight: 700, color: col, lineHeight: 1, transition: 'color 0.4s' }}>{score}</span>
          <span style={{ fontSize: 9, letterSpacing: 3, color: '#4a5568', marginTop: 2 }}>THREAT</span>
        </div>
      </div>
    </div>
  )
}

function Pulse({ active, color = '#30d158' }) {
  return (
    <span style={{ position: 'relative', display: 'inline-block', width: 10, height: 10 }}>
      <span style={{ position: 'absolute', inset: 0, borderRadius: '50%', background: color, opacity: active ? 0.3 : 0, animation: active ? 'pulse 1.4s ease-out infinite' : 'none' }} />
      <span style={{ position: 'absolute', inset: 2, borderRadius: '50%', background: active ? color : '#2d3748', transition: 'background 0.3s' }} />
    </span>
  )
}

function StatCard({ label, value, color = '#00d4ff', icon }) {
  return (
    <div style={{ background: '#0f1320', border: '1px solid #1e2535', borderRadius: 12, padding: '14px 18px', flex: 1 }}>
      <div style={{ fontSize: 10, letterSpacing: 2, color: '#4a5568', marginBottom: 6 }}>{icon} {label}</div>
      <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 26, fontWeight: 700, color }}>{value}</div>
    </div>
  )
}

const SCENES = {
  railway: { label: 'RAILWAY', icon: '🚆', color: '#007aff' },
  industrial: { label: 'INDUSTRIAL', icon: '🏭', color: '#ff9f0a' },
  aggression: { label: 'AGGRESSION', icon: '⚡', color: '#ff2d55' },
}

function SceneBadge({ scene }) {
  const m = SCENES[scene] || { label: (scene || 'UNKNOWN').toUpperCase(), icon: '📍', color: '#888' }
  return (
    <span style={{ background: m.color + '22', border: `1px solid ${m.color}44`, color: m.color, fontSize: 10, letterSpacing: 2, padding: '2px 8px', borderRadius: 4, fontFamily: "'Share Tech Mono',monospace" }}>
      {m.icon} {m.label}
    </span>
  )
}

function EventRow({ event, fresh }) {
  const col = scoreColor(event.threat_score)
  return (
    <tr style={{ borderBottom: '1px solid #0d1021', animation: fresh ? 'slideIn 0.3s ease' : 'none' }}>
      <td style={{ padding: '10px 14px', fontFamily: "'Share Tech Mono',monospace", color: '#4a90d9', fontSize: 12 }}>
        #{String(event.person_id).padStart(3, '0')}
      </td>
      <td style={{ padding: '10px 14px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: scoreBg(event.threat_score), border: `1px solid ${col}44`, borderRadius: 6, padding: '3px 10px' }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: col }} />
          <span style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 14, color: col, fontWeight: 700 }}>{event.threat_score}</span>
        </div>
      </td>
      <td style={{ padding: '10px 14px', color: '#cbd5e0', fontSize: 12 }}>{event.type}</td>
      <td style={{ padding: '10px 14px' }}><SceneBadge scene={event.scene} /></td>
      <td style={{ padding: '10px 14px', color: '#4a5568', fontSize: 11, fontFamily: "'Share Tech Mono',monospace" }}>
        {new Date(event.timestamp).toLocaleTimeString()}
      </td>
      <td style={{ padding: '10px 14px', color: '#4a5568', fontSize: 11 }}>
        {event.source_video ? event.source_video.replace(/^.*[\\/]/, '') : '—'}
      </td>
    </tr>
  )
}

function UploadZone({ onUpload, loading }) {
  const [drag, setDrag] = useState(false)
  const [scene, setScene] = useState('aggression')
  const ref = useRef()
  const go = (files) => { if (files?.[0]) onUpload(files[0], scene) }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', gap: 8 }}>
        {Object.entries(SCENES).map(([k, m]) => (
          <button key={k} onClick={() => setScene(k)} style={{
            flex: 1, padding: '8px 4px', borderRadius: 8, border: '1px solid',
            borderColor: scene === k ? m.color : '#1e2535',
            background: scene === k ? m.color + '18' : '#0f1320',
            color: scene === k ? m.color : '#4a5568',
            fontSize: 11, letterSpacing: 1.5, cursor: 'pointer',
            transition: 'all 0.2s', fontFamily: "'Share Tech Mono',monospace"
          }}>{m.icon} {m.label}</button>
        ))}
      </div>
      <div
        onDragOver={e => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); setDrag(false); go(e.dataTransfer.files) }}
        onClick={() => !loading && ref.current?.click()}
        style={{
          border: `2px dashed ${drag ? '#00d4ff' : '#1e2535'}`, borderRadius: 12,
          padding: '36px 24px', textAlign: 'center', cursor: loading ? 'wait' : 'pointer',
          background: drag ? 'rgba(0,212,255,0.04)' : '#090c14', transition: 'all 0.2s'
        }}
      >
        <input ref={ref} type="file" accept="video/*" style={{ display: 'none' }} onChange={e => go(e.target.files)} />
        {loading ? (
          <div>
            <div style={{ fontSize: 28, marginBottom: 10 }}>⏳</div>
            <div style={{ color: '#00d4ff', fontSize: 13, fontFamily: "'Share Tech Mono',monospace", letterSpacing: 2 }}>ANALYSING VIDEO...</div>
            <div style={{ color: '#4a5568', fontSize: 11, marginTop: 4 }}>Running detection pipeline</div>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: 32, marginBottom: 8 }}>🎬</div>
            <div style={{ color: '#718096', fontSize: 13 }}>Drop video clip or click to upload</div>
            <div style={{ color: '#2d3748', fontSize: 11, marginTop: 4 }}>MP4 · AVI · MOV · MKV</div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [online, setOnline] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const prevLen = useRef(0)

  const loadEvents = useCallback(async () => {
    try { const d = await fetchEvents(); setEvents(d.items || []) } catch { /* silent */ }
  }, [])

  useEffect(() => {
    fetchHealth().then(() => setOnline(true)).catch(() => setOnline(false))
  }, [])

  useEffect(() => {
    loadEvents()
    if (!autoRefresh) return
    const id = setInterval(loadEvents, 5000)
    return () => clearInterval(id)
  }, [autoRefresh, loadEvents])

  const handleUpload = async (file, scene) => {
    setLoading(true); setError(''); setResult(null)
    try {
      const r = await analyzeVideo(file, scene)
      setResult(r)
      await loadEvents()
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  const handleClear = async () => { await clearEvents(); setEvents([]); setResult(null) }

  const maxScore = events.length ? Math.max(...events.map(e => e.threat_score)) : 0
  const alerts = events.filter(e => e.threat_score >= 60).length
  const persons = new Set(events.map(e => e.person_id)).size
  const freshSet = new Set(events.slice(0, result?.events?.length || 0).map(e => e.timestamp))

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow:wght@400;500;600&display=swap');
        *{box-sizing:border-box;margin:0;padding:0}
        body{background:#07090f;color:#e2e8f0;font-family:'Barlow',sans-serif}
        @keyframes pulse{0%{transform:scale(1);opacity:.4}100%{transform:scale(2.8);opacity:0}}
        @keyframes slideIn{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}
        ::-webkit-scrollbar{width:4px}
        ::-webkit-scrollbar-track{background:#0d1021}
        ::-webkit-scrollbar-thumb{background:#1e2535;border-radius:2px}
      `}</style>

      <div style={{ minHeight: '100vh' }}>
        {/* Header */}
        <header style={{ background: '#090c14', borderBottom: '1px solid #141928', padding: '0 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 58 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span style={{ fontSize: 22 }}>🛡️</span>
            <div>
              <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 14, letterSpacing: 4, color: '#00d4ff' }}>ZERODAY</div>
              <div style={{ fontSize: 9, letterSpacing: 3, color: '#2d3748' }}>CCTV THREAT DETECTION</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Pulse active={online === true} color={online === false ? '#ff2d55' : '#30d158'} />
              <span style={{ fontSize: 11, color: online ? '#30d158' : online === false ? '#ff2d55' : '#4a5568', letterSpacing: 1, fontFamily: "'Share Tech Mono',monospace" }}>
                {online === null ? 'CONNECTING' : online ? 'BACKEND ONLINE' : 'OFFLINE'}
              </span>
            </div>
          </div>
        </header>

        <div style={{ maxWidth: 1320, margin: '0 auto', padding: '28px 24px', display: 'flex', gap: 22, flexWrap: 'wrap' }}>

          {/* Left */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18, flex: '0 0 270px' }}>
            {/* Gauge */}
            <div style={{ background: '#0f1320', border: '1px solid #1e2535', borderRadius: 16, padding: '22px 22px 18px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
              <div style={{ fontSize: 10, letterSpacing: 3, color: '#4a5568', alignSelf: 'flex-start' }}>LIVE THREAT LEVEL</div>
              <ThreatGauge score={maxScore} />
              <div style={{
                fontFamily: "'Share Tech Mono',monospace", fontSize: 12, letterSpacing: 2,
                color: scoreColor(maxScore), background: scoreBg(maxScore),
                border: `1px solid ${scoreColor(maxScore)}33`, padding: '6px 18px', borderRadius: 6
              }}>
                {maxScore >= 80 ? '⚠ HIGH THREAT' : maxScore >= 60 ? '⚡ SUSPICIOUS' : maxScore >= 40 ? '◈ MODERATE' : '✓ NOMINAL'}
              </div>
            </div>

            {/* Stats */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <StatCard label="TOTAL EVENTS" value={events.length} color="#00d4ff" icon="📋" />
              <StatCard label="ALERTS ≥60" value={alerts} color="#ff9f0a" icon="🚨" />
              <StatCard label="PERSONS" value={persons} color="#bf5af2" icon="👤" />
            </div>

            {/* Controls */}
            <div style={{ background: '#0f1320', border: '1px solid #1e2535', borderRadius: 16, padding: 18, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ fontSize: 10, letterSpacing: 3, color: '#4a5568' }}>CONTROLS</div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, color: '#718096' }}>
                <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} style={{ accentColor: '#00d4ff' }} />
                Auto-refresh (5s)
              </label>
              <button onClick={loadEvents} style={{ background: '#141928', border: '1px solid #1e2535', color: '#00d4ff', borderRadius: 8, padding: '8px 14px', fontSize: 11, letterSpacing: 1.5, cursor: 'pointer', fontFamily: "'Share Tech Mono',monospace" }}>
                ↻ REFRESH
              </button>
              <button onClick={handleClear} style={{ background: 'rgba(255,45,85,0.08)', border: '1px solid rgba(255,45,85,0.2)', color: '#ff2d55', borderRadius: 8, padding: '8px 14px', fontSize: 11, letterSpacing: 1.5, cursor: 'pointer', fontFamily: "'Share Tech Mono',monospace" }}>
                ✕ CLEAR ALL
              </button>
            </div>
          </div>

          {/* Right */}
          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 18 }}>

            {/* Upload */}
            <div style={{ background: '#0f1320', border: '1px solid #1e2535', borderRadius: 16, padding: 22 }}>
              <div style={{ fontSize: 10, letterSpacing: 3, color: '#4a5568', marginBottom: 14 }}>📤 UPLOAD VIDEO CLIP</div>
              <UploadZone onUpload={handleUpload} loading={loading} />
              {error && (
                <div style={{ marginTop: 12, background: 'rgba(255,45,85,0.08)', border: '1px solid rgba(255,45,85,0.2)', color: '#ff6b7a', borderRadius: 8, padding: '10px 14px', fontSize: 12 }}>
                  ⚠ {error}
                </div>
              )}
            </div>

            {/* Analysis result */}
            {result && (
              <div style={{ background: 'rgba(0,212,255,0.05)', border: '1px solid rgba(0,212,255,0.18)', borderRadius: 16, padding: '18px 22px', animation: 'slideIn 0.4s ease' }}>
                <div style={{ fontSize: 10, letterSpacing: 3, color: '#00d4ff', marginBottom: 14 }}>✓ ANALYSIS COMPLETE — {result.message}</div>
                <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap' }}>
                  {[['FRAMES', result.total_frames], ['PERSONS', result.persons_detected], ['ALERTS', result.alerts], ['MAX SCORE', result.max_threat_score]].map(([l, v]) => (
                    <div key={l}>
                      <div style={{ fontSize: 9, letterSpacing: 2, color: '#4a5568' }}>{l}</div>
                      <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 22, color: l === 'MAX SCORE' ? scoreColor(v) : '#e2e8f0' }}>{v}</div>
                    </div>
                  ))}
                  <div>
                    <div style={{ fontSize: 9, letterSpacing: 2, color: '#4a5568', marginBottom: 4 }}>SCENE</div>
                    <SceneBadge scene={result.scene} />
                  </div>
                </div>
              </div>
            )}

            {/* Events table */}
            <div style={{ background: '#0f1320', border: '1px solid #1e2535', borderRadius: 16, overflow: 'hidden', flex: 1 }}>
              <div style={{ padding: '14px 20px', borderBottom: '1px solid #141928', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: 10, letterSpacing: 3, color: '#4a5568' }}>📋 THREAT LOG</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Pulse active={autoRefresh} color="#00d4ff" />
                  <span style={{ fontSize: 11, color: '#2d3748', fontFamily: "'Share Tech Mono',monospace" }}>{events.length} RECORDS</span>
                </div>
              </div>
              <div style={{ overflowX: 'auto', maxHeight: 500, overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      {['PERSON', 'SCORE', 'TYPE', 'SCENE', 'TIME', 'SOURCE'].map(h => (
                        <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 9, letterSpacing: 2, color: '#2d3748', fontWeight: 600, position: 'sticky', top: 0, background: '#0f1320', borderBottom: '1px solid #141928' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {events.length === 0 ? (
                      <tr><td colSpan={6} style={{ padding: '48px', textAlign: 'center', color: '#2d3748', fontSize: 13 }}>No events. Upload a video clip to begin.</td></tr>
                    ) : (
                      events.map((ev, i) => <EventRow key={`${ev.timestamp}-${ev.person_id}-${i}`} event={ev} fresh={i < (result?.alerts || 0)} />)
                    )}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        </div>
      </div>
    </>
  )
}
