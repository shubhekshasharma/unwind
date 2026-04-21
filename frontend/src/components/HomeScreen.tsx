import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Settings as SettingsIcon, Edit3, RotateCcw, SlidersHorizontal, Moon } from 'lucide-react'
import { UnwindLogo } from './UnwindLogo'
import type { Prefs, SessionState, SendCmd } from '../App'

type Props = { prefs: Prefs; session: SessionState; sendCmd: SendCmd }

const DURATIONS = [15, 20, 30, 45, 60]

function fmt12h(t: string): string {
  try {
    const [h, m] = t.split(':').map(Number)
    const period = h >= 12 ? 'PM' : 'AM'
    return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${period}`
  } catch {
    return t
  }
}

export function HomeScreen({ prefs, sendCmd }: Props) {
  const [showSettings, setShowSettings] = useState(false)
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const [showDebug, setShowDebug] = useState(false)
  const [edit, setEdit] = useState({ ...prefs })
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  // Reset edit state when modal opens
  const openSettings = () => {
    setEdit({ ...prefs })
    setShowSettings(true)
  }

  const saveSettings = () => {
    sendCmd({
      cmd: 'set_prefs',
      prefs: {
        bedtime: edit.bedtime,
        wakeTime: edit.wakeTime,
        unwindDuration: edit.unwindDuration,
        onboardingComplete: true,
      },
    })
    setShowSettings(false)
  }

  const timeStr = now.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })

  const dayProgress = ((now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds()) / 86400) * 628

  return (
    <div className="size-full relative overflow-hidden bg-slate-950">
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            'radial-gradient(circle at 50% 30%, rgba(251,146,60,0.07) 0%, transparent 60%)',
            'radial-gradient(circle at 50% 35%, rgba(245,158,11,0.09) 0%, transparent 60%)',
            'radial-gradient(circle at 50% 30%, rgba(251,146,60,0.07) 0%, transparent 60%)',
          ],
        }}
        transition={{ duration: 10, repeat: Infinity }}
      />

      <div className="relative size-full flex flex-col p-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <UnwindLogo size={36} animate />
            <span className="text-base leading-none text-orange-300/90 tracking-wide" style={{ fontWeight: 500 }}>Unwind</span>
          </div>
          <button
            onClick={openSettings}
            className="p-2.5 rounded-full hover:bg-orange-900/20 transition-colors"
          >
            <SettingsIcon className="w-6 h-6 text-orange-400/75" />
          </button>
        </div>

        {/* Clock */}
        <div className="flex-1 flex flex-col items-center justify-center -mt-2">
          {/* Container sized to the ring so text stays inside it */}
          <div className="relative w-64 h-64 mx-auto mb-5 flex items-center justify-center">
            <svg
              viewBox="0 0 208 208"
              className="absolute inset-0 w-full h-full -rotate-90"
              style={{ filter: 'blur(0.3px)' }}
            >
              <circle cx="104" cy="104" r="100" stroke="rgba(251,146,60,0.10)" strokeWidth="2.5" fill="none" />
              <motion.circle
                cx="104" cy="104" r="100"
                stroke="url(#tg)" strokeWidth="2.5" fill="none"
                strokeDasharray={628}
                strokeDashoffset={628 - dayProgress}
                strokeLinecap="round"
              />
              <defs>
                <linearGradient id="tg" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="rgba(251,146,60,0.50)" />
                  <stop offset="100%" stopColor="rgba(245,158,11,0.70)" />
                </linearGradient>
              </defs>
            </svg>

            <motion.div
              animate={{ opacity: [0.95, 1, 0.95] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="text-center relative z-10"
            >
              <div
                className="text-5xl leading-none text-white tracking-tight tabular-nums"
                style={{ fontWeight: 300 }}
              >
                {timeStr}
              </div>
              <div className="text-sm text-orange-300/65 mt-3 tracking-wide" style={{ fontWeight: 400 }}>
                {now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </div>
            </motion.div>
          </div>
        </div>

        {/* Schedule cards */}
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-sm tracking-widest uppercase text-orange-400/65" style={{ fontWeight: 600 }}>
              Schedule
            </span>
            <button
              onClick={openSettings}
              className="flex items-center gap-1.5 text-sm text-orange-400/70 hover:text-orange-300 transition-colors px-2 py-1"
            >
              <Edit3 className="w-4 h-4" /> Edit
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2.5">
            <div className="bg-gradient-to-br from-orange-950/30 to-orange-900/20 border border-orange-800/25 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-xs tracking-wider uppercase text-orange-400/70 mb-2" style={{ fontWeight: 600 }}>Bedtime</div>
              <div className="text-lg text-orange-100 tabular-nums" style={{ fontWeight: 500 }}>{fmt12h(prefs.bedtime)}</div>
            </div>
            <div className="bg-gradient-to-br from-amber-950/30 to-amber-900/20 border border-amber-800/25 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-xs tracking-wider uppercase text-amber-400/70 mb-2" style={{ fontWeight: 600 }}>Wake</div>
              <div className="text-lg text-amber-100 tabular-nums" style={{ fontWeight: 500 }}>{fmt12h(prefs.wakeTime)}</div>
            </div>
            <div className="bg-gradient-to-br from-rose-950/30 to-rose-900/20 border border-rose-800/25 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-xs tracking-wider uppercase text-rose-400/70 mb-2" style={{ fontWeight: 600 }}>Ritual</div>
              <div className="text-lg text-rose-100" style={{ fontWeight: 500 }}>{prefs.unwindDuration}m</div>
            </div>
          </div>

          <button
            onClick={() => sendCmd({ cmd: 'navigate', screen: 'stats' })}
            className="w-full py-3 rounded-2xl bg-orange-950/20 border border-orange-800/15 text-orange-300/70 hover:text-orange-200 hover:bg-orange-950/30 transition-colors text-sm mt-1"
            style={{ fontWeight: 400 }}
          >
            View sleep history
          </button>
        </div>
      </div>

      {/* Debug menu — bottom right */}
      <div className="absolute bottom-4 right-4 z-20">
        <button
          onClick={() => setShowDebug(d => !d)}
          className="w-8 h-8 rounded-full bg-white/5 border border-white/8 flex items-center justify-center hover:bg-white/10 transition-colors"
        >
          <SlidersHorizontal className="w-3.5 h-3.5 text-slate-500" />
        </button>
        <AnimatePresence>
          {showDebug && (
            <motion.div
              initial={{ opacity: 0, scale: 0.92, y: 6 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.92, y: 6 }}
              transition={{ duration: 0.15 }}
              className="absolute bottom-10 right-0 bg-slate-900/95 border border-slate-700/50 rounded-xl p-3 w-48"
            >
              <p className="text-xs text-slate-500 mb-2 tracking-wide uppercase">Simulate</p>
              <button
                onClick={() => { sendCmd({ cmd: 'start_session' }); setShowDebug(false) }}
                className="w-full text-left text-sm text-slate-300 hover:text-white px-2 py-1.5 rounded-lg hover:bg-white/5 transition-colors flex items-center gap-2"
              >
                <Moon className="w-3.5 h-3.5 shrink-0" />
                Start unwind now
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Settings modal */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/75 backdrop-blur-md flex items-center justify-center p-5 z-10"
            onClick={() => setShowSettings(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-gradient-to-b from-orange-950/60 to-slate-900/98 rounded-2xl p-6 w-full max-w-sm border border-orange-900/40"
            >
              <h2 className="text-xl text-white mb-5" style={{ fontWeight: 500 }}>Edit schedule</h2>
              <div className="space-y-4 mb-5">
                <div className="space-y-1.5">
                  <label className="text-sm text-orange-200/85" style={{ fontWeight: 500 }}>Bedtime</label>
                  <input
                    type="time"
                    value={edit.bedtime}
                    onChange={(e) => setEdit({ ...edit, bedtime: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl bg-orange-950/30 border border-orange-800/45 text-white focus:outline-none focus:border-orange-500/70 transition-colors"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm text-orange-200/85" style={{ fontWeight: 500 }}>Wake time</label>
                  <input
                    type="time"
                    value={edit.wakeTime}
                    onChange={(e) => setEdit({ ...edit, wakeTime: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl bg-orange-950/30 border border-orange-800/45 text-white focus:outline-none focus:border-orange-500/70 transition-colors"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm text-orange-200/85" style={{ fontWeight: 500 }}>Ritual duration</label>
                  <select
                    value={edit.unwindDuration}
                    onChange={(e) => setEdit({ ...edit, unwindDuration: Number(e.target.value) })}
                    className="w-full px-4 py-3 rounded-xl bg-orange-950/30 border border-orange-800/45 text-white focus:outline-none focus:border-orange-500/70 transition-colors"
                  >
                    {DURATIONS.map((d) => (
                      <option key={d} value={d}>{d} minutes</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="space-y-2.5">
                <button
                  onClick={saveSettings}
                  className="w-full py-3.5 rounded-xl bg-orange-700/80 hover:bg-orange-700 text-orange-50 transition-colors"
                  style={{ fontWeight: 500 }}
                >
                  Save changes
                </button>
                <button
                  onClick={() => setShowSettings(false)}
                  className="w-full py-2.5 text-orange-300/55 hover:text-orange-200/80 transition-colors text-sm"
                  style={{ fontWeight: 400 }}
                >
                  Cancel
                </button>
                <div className="pt-1 border-t border-orange-900/30">
                  <button
                    onClick={() => { setShowSettings(false); setShowResetConfirm(true) }}
                    className="w-full mt-2 py-2 flex items-center justify-center gap-2 text-sm text-red-400/55 hover:text-red-300/80 transition-colors"
                    style={{ fontWeight: 400 }}
                  >
                    <RotateCcw className="w-3 h-3" />
                    Reset app &amp; clear data
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reset confirmation */}
      <AnimatePresence>
        {showResetConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-5 z-20"
            onClick={() => setShowResetConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-gradient-to-b from-red-950/60 to-slate-900/98 rounded-2xl p-6 w-full max-w-sm border border-red-900/40"
            >
              <h2 className="text-xl text-white mb-2" style={{ fontWeight: 500 }}>Reset everything?</h2>
              <p className="text-red-200/80 text-sm mb-6" style={{ fontWeight: 400 }}>
                This will erase all session history, clear your schedule, and restart onboarding. This cannot be undone.
              </p>
              <div className="space-y-2.5">
                <button
                  onClick={() => { sendCmd({ cmd: 'reset' }); setShowResetConfirm(false) }}
                  className="w-full py-3.5 rounded-xl bg-red-700 hover:bg-red-600 text-white transition-colors"
                  style={{ fontWeight: 500 }}
                >
                  Yes, reset everything
                </button>
                <button
                  onClick={() => setShowResetConfirm(false)}
                  className="w-full py-2.5 text-orange-300/55 hover:text-orange-200/80 transition-colors text-sm"
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
