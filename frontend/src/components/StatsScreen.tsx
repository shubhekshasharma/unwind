import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { ArrowLeft, Moon, RotateCcw } from 'lucide-react'
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
      .then((data) => {
        setSessions(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const avgDuration = sessions.length
    ? sessions.reduce((s, r) => s + (r.duration_seconds || 0), 0) / sessions.length
    : 0

  return (
    <div className="size-full relative overflow-hidden bg-slate-950">
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            'radial-gradient(circle at 50% 10%, rgba(251,146,60,0.07) 0%, transparent 50%)',
            'radial-gradient(circle at 50% 10%, rgba(251,146,60,0.04) 0%, transparent 50%)',
            'radial-gradient(circle at 50% 10%, rgba(251,146,60,0.07) 0%, transparent 50%)',
          ],
        }}
        transition={{ duration: 8, repeat: Infinity }}
      />

      <div className="relative size-full flex flex-col p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => sendCmd({ cmd: 'navigate', screen: 'home' })}
              className="p-2 rounded-full hover:bg-orange-900/20 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-orange-400/70" />
            </button>
            <h1 className="text-xl text-white" style={{ fontWeight: 400 }}>Sleep history</h1>
          </div>
          <button
            onClick={() => setShowResetConfirm(true)}
            className="flex items-center gap-1.5 text-xs text-red-400/40 hover:text-red-400/70 transition-colors px-3 py-1.5 rounded-full hover:bg-red-950/20"
            style={{ fontWeight: 400 }}
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </button>
        </div>

        {/* Summary row */}
        {sessions.length > 0 && (
          <div className="grid grid-cols-2 gap-3 mb-5">
            <div className="bg-orange-950/20 border border-orange-800/20 rounded-2xl p-4">
              <div className="text-xs uppercase tracking-wider text-orange-400/50 mb-1" style={{ fontWeight: 500 }}>Sessions</div>
              <div className="text-2xl text-white" style={{ fontWeight: 300 }}>{sessions.length}</div>
            </div>
            <div className="bg-amber-950/20 border border-amber-800/20 rounded-2xl p-4">
              <div className="text-xs uppercase tracking-wider text-amber-400/50 mb-1" style={{ fontWeight: 500 }}>Avg duration</div>
              <div className="text-2xl text-white" style={{ fontWeight: 300 }}>{fmtDuration(avgDuration)}</div>
            </div>
          </div>
        )}

        {/* Session list */}
        <div className="flex-1 overflow-y-auto space-y-3 pb-2">
          {loading && (
            <div className="text-center text-orange-400/40 pt-12 text-sm">Loading…</div>
          )}

          {!loading && sessions.length === 0 && (
            <div className="flex flex-col items-center justify-center pt-12 gap-4">
              <Moon className="w-12 h-12 text-orange-400/20" />
              <p className="text-orange-200/40 text-sm text-center" style={{ fontWeight: 350 }}>
                No completed sessions yet.{'\n'}Complete your first Unwind ritual to see stats here.
              </p>
            </div>
          )}

          {sessions.map((s, i) => {
            const pickups = s.pickup_count || 0
            const pickupColor = pickups === 0 ? 'text-green-400/80' : pickups > 2 ? 'text-red-400/80' : 'text-orange-400/70'

            return (
              <motion.div
                key={s.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="bg-gradient-to-br from-orange-950/20 to-slate-950/40 border border-orange-800/15 rounded-2xl p-5"
              >
                <div className="text-xs text-orange-400/40 mb-2" style={{ fontWeight: 400 }}>
                  {s.created_at || '—'}
                </div>
                <div className="text-xl text-white mb-3" style={{ fontWeight: 350 }}>
                  Unwound for{' '}
                  <span style={{ fontWeight: 500 }}>{fmtDuration(s.duration_seconds)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className={pickupColor} style={{ fontWeight: 350 }}>
                    {pickups === 0 ? 'No pickups ✓' : `${pickups} pickup${pickups !== 1 ? 's' : ''}`}
                  </span>
                  {s.alarm_time && (
                    <span className="text-amber-400/50" style={{ fontWeight: 350 }}>
                      Bedtime {fmt12h(s.alarm_time)}
                    </span>
                  )}
                </div>
              </motion.div>
            )
          })}
        </div>
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
              className="bg-gradient-to-b from-red-950/95 to-slate-950/95 rounded-3xl p-7 w-full border border-red-800/30"
            >
              <h2 className="text-xl text-white mb-2" style={{ fontWeight: 400 }}>Reset everything?</h2>
              <p className="text-red-200/60 text-sm mb-6" style={{ fontWeight: 350 }}>
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
