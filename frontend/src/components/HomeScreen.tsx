import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Settings as SettingsIcon, RotateCcw, History } from 'lucide-react'
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

function unwindStartTime(bedtime: string, duration: number): string {
  try {
    const [h, m] = bedtime.split(':').map(Number)
    const total = ((h * 60 + m - duration) % 1440 + 1440) % 1440
    const sh = Math.floor(total / 60)
    const sm = total % 60
    return fmt12h(`${String(sh).padStart(2, '0')}:${String(sm).padStart(2, '0')}`)
  } catch { return '' }
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

  return (
    <div className="size-full relative overflow-hidden bg-slate-950">
      <motion.div
        className="absolute inset-0 pointer-events-none"
        animate={{
          background: [
            'radial-gradient(circle at 50% 35%, rgba(251,146,60,0.07) 0%, transparent 55%)',
            'radial-gradient(circle at 50% 40%, rgba(245,158,11,0.09) 0%, transparent 55%)',
            'radial-gradient(circle at 50% 35%, rgba(251,146,60,0.07) 0%, transparent 55%)',
          ],
        }}
        transition={{ duration: 10, repeat: Infinity }}
      />

      <div className="relative size-full flex flex-col">
        {/* Header */}
        <div className="relative z-10 flex items-center justify-between px-6 pt-5">
          <div className="flex items-center gap-2.5">
            <UnwindLogo size={28} animate />
            <span className="text-sm text-orange-300/80 tracking-wide" style={{ fontWeight: 500 }}>Unwind</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => sendCmd({ cmd: 'navigate', screen: 'stats' })}
              className="w-10 h-10 rounded-full bg-orange-950/35 flex items-center justify-center hover:bg-orange-950/55 transition-colors"
            >
              <History className="w-5 h-5 text-orange-400/80" />
            </button>
            <button
              onClick={openSettings}
              className="w-10 h-10 rounded-full bg-orange-950/35 flex items-center justify-center hover:bg-orange-950/55 transition-colors"
            >
              <SettingsIcon className="w-5 h-5 text-orange-400/80" />
            </button>
          </div>
        </div>

        {/* Clock + schedule — centered */}
        <div className="flex-1 flex flex-col items-center justify-center -mt-8">
          <motion.div
            animate={{ opacity: [0.95, 1, 0.95] }}
            transition={{ duration: 4, repeat: Infinity }}
            className="text-center"
          >
            <div
              className="text-7xl leading-none text-white tabular-nums mb-2"
              style={{ fontFamily: '"DM Sans", sans-serif', fontWeight: 300, letterSpacing: '-0.02em' }}
            >
              {timeStr}
            </div>
            <div className="text-base text-white/60 tracking-wide mb-2" style={{ fontWeight: 400 }}>
              {now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
            </div>
            <div className="text-sm text-orange-400/70 tracking-wide mb-10 mt-3" style={{ fontWeight: 400 }}>
              Unwind begins at {unwindStartTime(prefs.bedtime, prefs.unwindDuration)}
            </div>
          </motion.div>

          {/* Schedule row */}
          <div className="flex items-center gap-6 text-orange-300/40">
            <button
              onClick={openSettings}
              className="flex flex-col items-center gap-1.5 hover:text-orange-300/70 transition-colors group min-w-[80px] py-2"
            >
              <div className="text-xs tracking-wide text-orange-400/50 group-hover:text-orange-400/80 transition-colors" style={{ fontWeight: 600 }}>
                BEDTIME
              </div>
              <div className="text-xl text-orange-200/70 group-hover:text-orange-200 transition-colors" style={{ fontWeight: 400 }}>
                {fmt12h(prefs.bedtime)}
              </div>
            </button>

            <div className="w-px h-10 bg-orange-800/20" />

            <button
              onClick={openSettings}
              className="flex flex-col items-center gap-1.5 hover:text-orange-300/70 transition-colors group min-w-[80px] py-2"
            >
              <div className="text-xs tracking-wide text-amber-400/50 group-hover:text-amber-400/80 transition-colors" style={{ fontWeight: 600 }}>
                WAKE UP
              </div>
              <div className="text-xl text-amber-200/70 group-hover:text-amber-200 transition-colors" style={{ fontWeight: 400 }}>
                {fmt12h(prefs.wakeTime)}
              </div>
            </button>

            <div className="w-px h-10 bg-orange-800/20" />

            <button
              onClick={openSettings}
              className="flex flex-col items-center gap-1.5 hover:text-orange-300/70 transition-colors group min-w-[80px] py-2"
            >
              <div className="text-xs tracking-wide text-rose-400/50 group-hover:text-rose-400/80 transition-colors" style={{ fontWeight: 600 }}>
                RITUAL
              </div>
              <div className="text-xl text-rose-200/70 group-hover:text-rose-200 transition-colors" style={{ fontWeight: 400 }}>
                {prefs.unwindDuration}m
              </div>
            </button>
          </div>
        </div>

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
                  <label className="text-sm text-orange-200/85" style={{ fontWeight: 500 }}>Wake Up</label>
                  <input
                    type="time"
                    value={edit.wakeTime}
                    onChange={(e) => setEdit({ ...edit, wakeTime: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl bg-orange-950/30 border border-orange-800/45 text-white focus:outline-none focus:border-orange-500/70 transition-colors"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm text-orange-200/85" style={{ fontWeight: 500 }}>Ritual</label>
                  <select
                    value={edit.unwindDuration}
                    onChange={(e) => setEdit({ ...edit, unwindDuration: Number(e.target.value) })}
                    className="w-full pl-4 pr-10 py-3 rounded-xl bg-orange-950/30 border border-orange-800/45 text-white focus:outline-none focus:border-orange-500/70 transition-colors"
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
