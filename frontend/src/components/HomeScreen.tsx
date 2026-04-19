import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Settings as SettingsIcon, Edit3, RotateCcw } from 'lucide-react'
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
            'radial-gradient(circle at 50% 30%, rgba(251,146,60,0.1) 0%, transparent 60%)',
            'radial-gradient(circle at 50% 35%, rgba(245,158,11,0.13) 0%, transparent 60%)',
            'radial-gradient(circle at 50% 30%, rgba(251,146,60,0.1) 0%, transparent 60%)',
          ],
        }}
        transition={{ duration: 10, repeat: Infinity }}
      />

      <div className="relative size-full flex flex-col p-7">
        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <div className="flex items-center gap-3">
            <UnwindLogo size={26} animate />
            <span className="text-base text-orange-300/90 tracking-wide" style={{ fontWeight: 350 }}>Unwind</span>
          </div>
          <button
            onClick={openSettings}
            className="p-2.5 rounded-full hover:bg-orange-900/20 transition-colors"
          >
            <SettingsIcon className="w-5 h-5 text-orange-400/70" />
          </button>
        </div>

        {/* Clock */}
        <div className="flex-1 flex flex-col items-center justify-center -mt-6">
          <div className="relative mb-8">
            <svg className="w-52 h-52 -rotate-90 absolute inset-0" style={{ filter: 'blur(0.5px)' }}>
              <circle cx="104" cy="104" r="100" stroke="rgba(251,146,60,0.06)" strokeWidth="2" fill="none" />
              <motion.circle
                cx="104" cy="104" r="100"
                stroke="url(#tg)" strokeWidth="2" fill="none"
                strokeDasharray={628}
                strokeDashoffset={628 - dayProgress}
                strokeLinecap="round"
              />
              <defs>
                <linearGradient id="tg" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="rgba(251,146,60,0.35)" />
                  <stop offset="100%" stopColor="rgba(245,158,11,0.55)" />
                </linearGradient>
              </defs>
            </svg>

            <motion.div
              animate={{ opacity: [0.95, 1, 0.95] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="text-center relative"
            >
              <div
                className="text-[4.8rem] leading-none text-white tracking-tight tabular-nums"
                style={{ fontWeight: 250 }}
              >
                {timeStr}
              </div>
              <div className="text-sm text-orange-300/45 mt-4 tracking-wide" style={{ fontWeight: 400 }}>
                {now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </div>
            </motion.div>
          </div>
        </div>

        {/* Schedule cards */}
        <div className="space-y-3">
          <div className="flex items-baseline justify-between px-1">
            <span className="text-xs tracking-widest uppercase text-orange-400/50" style={{ fontWeight: 500 }}>
              Schedule
            </span>
            <button
              onClick={openSettings}
              className="flex items-center gap-1.5 text-xs text-orange-400/60 hover:text-orange-300 transition-colors"
            >
              <Edit3 className="w-3 h-3" /> Edit
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div className="bg-gradient-to-br from-orange-950/30 to-orange-900/20 border border-orange-800/20 rounded-2xl p-4 backdrop-blur-sm">
              <div className="text-[10px] tracking-wider uppercase text-orange-400/50 mb-2" style={{ fontWeight: 500 }}>Bedtime</div>
              <div className="text-xl text-orange-100" style={{ fontWeight: 400 }}>{fmt12h(prefs.bedtime)}</div>
            </div>
            <div className="bg-gradient-to-br from-amber-950/30 to-amber-900/20 border border-amber-800/20 rounded-2xl p-4 backdrop-blur-sm">
              <div className="text-[10px] tracking-wider uppercase text-amber-400/50 mb-2" style={{ fontWeight: 500 }}>Wake</div>
              <div className="text-xl text-amber-100" style={{ fontWeight: 400 }}>{fmt12h(prefs.wakeTime)}</div>
            </div>
            <div className="bg-gradient-to-br from-rose-950/30 to-rose-900/20 border border-rose-800/20 rounded-2xl p-4 backdrop-blur-sm">
              <div className="text-[10px] tracking-wider uppercase text-rose-400/50 mb-2" style={{ fontWeight: 500 }}>Ritual</div>
              <div className="text-xl text-rose-100" style={{ fontWeight: 400 }}>{prefs.unwindDuration}m</div>
            </div>
          </div>

          <button
            onClick={() => sendCmd({ cmd: 'navigate', screen: 'stats' })}
            className="w-full py-3 rounded-2xl bg-orange-950/20 border border-orange-800/15 text-orange-300/60 hover:text-orange-200 hover:bg-orange-950/30 transition-colors text-sm mt-1"
            style={{ fontWeight: 400 }}
          >
            View sleep history
          </button>
        </div>
      </div>

      {/* Settings modal */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-5 z-10"
            onClick={() => setShowSettings(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-gradient-to-b from-orange-950/95 to-slate-950/95 rounded-3xl p-7 w-full border border-orange-800/30 backdrop-blur-xl"
            >
              <h2 className="text-2xl text-white mb-6" style={{ fontWeight: 400 }}>Edit schedule</h2>
              <div className="space-y-4 mb-6">
                <div className="space-y-2">
                  <label className="text-sm text-orange-200/70" style={{ fontWeight: 500 }}>Bedtime</label>
                  <input
                    type="time"
                    value={edit.bedtime}
                    onChange={(e) => setEdit({ ...edit, bedtime: e.target.value })}
                    className="w-full px-4 py-3 rounded-2xl bg-orange-950/40 border border-orange-800/40 text-white focus:outline-none focus:border-orange-600/60 transition-colors"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-orange-200/70" style={{ fontWeight: 500 }}>Wake time</label>
                  <input
                    type="time"
                    value={edit.wakeTime}
                    onChange={(e) => setEdit({ ...edit, wakeTime: e.target.value })}
                    className="w-full px-4 py-3 rounded-2xl bg-orange-950/40 border border-orange-800/40 text-white focus:outline-none focus:border-orange-600/60 transition-colors"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-orange-200/70" style={{ fontWeight: 500 }}>Ritual duration</label>
                  <select
                    value={edit.unwindDuration}
                    onChange={(e) => setEdit({ ...edit, unwindDuration: Number(e.target.value) })}
                    className="w-full px-4 py-3 rounded-2xl bg-orange-950/40 border border-orange-800/40 text-white focus:outline-none focus:border-orange-600/60 transition-colors"
                  >
                    {DURATIONS.map((d) => (
                      <option key={d} value={d}>{d} minutes</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="space-y-3">
                <button
                  onClick={saveSettings}
                  className="w-full py-3.5 rounded-2xl bg-orange-600 hover:bg-orange-500 text-white transition-colors"
                  style={{ fontWeight: 500 }}
                >
                  Save changes
                </button>
                <button
                  onClick={() => setShowSettings(false)}
                  className="w-full py-2.5 text-orange-300/70 hover:text-orange-200 transition-colors text-sm"
                  style={{ fontWeight: 400 }}
                >
                  Cancel
                </button>
                <button
                  onClick={() => { setShowSettings(false); setShowResetConfirm(true) }}
                  className="w-full py-2.5 flex items-center justify-center gap-1.5 text-red-400/50 hover:text-red-400/80 transition-colors text-xs"
                  style={{ fontWeight: 400 }}
                >
                  <RotateCcw className="w-3 h-3" />
                  Reset app &amp; clear data
                </button>
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
            className="absolute inset-0 bg-black/85 backdrop-blur-md flex items-center justify-center p-5 z-20"
            onClick={() => setShowResetConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-gradient-to-b from-red-950/95 to-slate-950/95 rounded-3xl p-7 w-full border border-red-800/30 backdrop-blur-xl"
            >
              <h2 className="text-xl text-white mb-2" style={{ fontWeight: 400 }}>Reset everything?</h2>
              <p className="text-red-200/60 text-sm mb-6" style={{ fontWeight: 350 }}>
                This will erase all session history, clear your schedule, and restart onboarding. This cannot be undone.
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
