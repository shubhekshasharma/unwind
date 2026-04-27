import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { X, Moon } from 'lucide-react'
import type { Prefs, SendCmd } from '../App'

type Props = { prefs: Prefs; sendCmd: SendCmd }

type SessionRow = {
  id: number
  created_at: string
  duration_seconds: number
  pickup_count: number
  alarm_time: string
}

function fmt12h(t: string): string {
  try {
    const [h, m] = t.split(':').map(Number)
    return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h >= 12 ? 'PM' : 'AM'}`
  } catch { return t }
}

function fmtDuration(secs: number): string {
  if (!secs) return '—'
  const m = Math.floor(secs / 60)
  const h = Math.floor(m / 60)
  if (h > 0) return `${h}h ${String(m % 60).padStart(2, '0')}m`
  return `${m}m`
}

export function StatsScreen({ sendCmd }: Props) {
  const [sessions, setSessions] = useState<SessionRow[]>([])
  const [loading, setLoading] = useState(true)
  const [showResetConfirm, setShowResetConfirm] = useState(false)

  useEffect(() => {
    fetch('/api/sessions')
      .then((r) => r.json())
      .then((data) => { setSessions(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const avgPickups = sessions.length
    ? Math.round(sessions.reduce((s, r) => s + (r.pickup_count || 0), 0) / sessions.length)
    : 0

  return (
    <div className="size-full relative overflow-hidden bg-slate-950">
      <motion.div
        className="absolute inset-0 pointer-events-none"
        animate={{
          background: [
            'radial-gradient(circle at 50% 20%, rgba(251,146,60,0.06) 0%, transparent 60%)',
            'radial-gradient(circle at 50% 25%, rgba(245,158,11,0.08) 0%, transparent 60%)',
            'radial-gradient(circle at 50% 20%, rgba(251,146,60,0.06) 0%, transparent 60%)',
          ],
        }}
        transition={{ duration: 12, repeat: Infinity }}
      />

      <div className="relative size-full flex flex-col p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-3xl text-white" style={{ fontWeight: 500 }}>History</h1>
            {sessions.length > 0 && (
              <div className="flex items-center gap-3 mt-3">
                <span className="text-sm text-orange-300/60" style={{ fontWeight: 400 }}>
                  {sessions.length} session{sessions.length !== 1 ? 's' : ''}
                </span>
                <div className="w-1 h-1 rounded-full bg-orange-400/30" />
                <span className="text-sm text-orange-300/60" style={{ fontWeight: 400 }}>
                  {avgPickups} avg pickup{avgPickups !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>
          <button
            onClick={() => sendCmd({ cmd: 'navigate', screen: 'home' })}
            className="p-2.5 rounded-full hover:bg-orange-900/20 transition-colors"
          >
            <X className="w-5 h-5 text-orange-400/80" />
          </button>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto space-y-5 pb-4">
          {loading && (
            <div className="text-center text-orange-400/50 pt-16 text-sm">Loading…</div>
          )}

          {!loading && sessions.length === 0 && (
            <div className="flex flex-col items-center justify-center pt-16 gap-4">
              <Moon className="w-10 h-10 text-orange-400/30" />
              <p className="text-orange-200/50 text-sm text-center" style={{ fontWeight: 400 }}>
                No sessions yet.{'\n'}Complete your first Unwind to see history here.
              </p>
            </div>
          )}

          {sessions.map((s, i) => {
            const pickups = s.pickup_count || 0
            return (
              <motion.div
                key={s.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="border-l-2 border-orange-800/25 pl-5 py-1"
              >
                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-base text-orange-200/70" style={{ fontWeight: 400 }}>
                    {s.created_at || '—'}
                  </span>
                  <span className="text-sm text-orange-300/60" style={{ fontWeight: 400 }}>
                    {fmtDuration(s.duration_seconds)}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  {s.alarm_time && (
                    <span className="text-slate-500" style={{ fontWeight: 400 }}>
                      {fmt12h(s.alarm_time)}
                    </span>
                  )}
                  {s.alarm_time && <div className="w-1 h-1 rounded-full bg-slate-700" />}
                  <span
                    className={pickups === 0 ? 'text-green-400/75' : 'text-slate-500'}
                    style={{ fontWeight: 400 }}
                  >
                    {pickups === 0 ? 'No pickups' : `${pickups} pickup${pickups !== 1 ? 's' : ''}`}
                  </span>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Reset link */}
        {sessions.length > 0 && (
          <button
            onClick={() => setShowResetConfirm(true)}
            className="mt-4 text-xs text-red-400/40 hover:text-red-400/70 transition-colors text-center"
            style={{ fontWeight: 400 }}
          >
            Reset all data
          </button>
        )}
      </div>

      {/* Reset confirmation modal */}
      <AnimatePresence>
        {showResetConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/85 backdrop-blur-md flex items-center justify-center p-5 z-10"
            onClick={() => setShowResetConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-gradient-to-b from-red-950/95 to-slate-950/95 rounded-3xl p-7 w-full max-w-sm border border-red-800/30"
            >
              <h2 className="text-xl text-white mb-2" style={{ fontWeight: 400 }}>Reset everything?</h2>
              <p className="text-red-200/75 text-sm mb-6" style={{ fontWeight: 400 }}>
                This will erase all {sessions.length} session{sessions.length !== 1 ? 's' : ''}, clear your schedule, and restart onboarding. This cannot be undone.
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => { sendCmd({ cmd: 'reset' }); setShowResetConfirm(false) }}
                  className="w-full py-3.5 rounded-2xl bg-red-700 hover:bg-red-600 text-white transition-colors"
                  style={{ fontWeight: 500 }}
                >
                  Yes, reset everything
                </button>
                <button
                  onClick={() => setShowResetConfirm(false)}
                  className="w-full py-2.5 text-orange-300/70 hover:text-orange-200 transition-colors text-sm"
                  style={{ fontWeight: 400 }}
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
