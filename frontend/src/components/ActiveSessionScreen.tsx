import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Sparkles, X, Phone } from 'lucide-react'
import { UnwindLogo } from './UnwindLogo'
import type { Prefs, SessionState, SendCmd } from '../App'

type Props = { prefs: Prefs; session: SessionState; sendCmd: SendCmd }

const NUDGES = [
  'Try some deep breathing',
  'Journal about your day',
  'Read a few pages of your book',
  'Note three things you\'re grateful for',
  'Gently stretch your neck and shoulders',
  'Reflect on something that went well today',
  'Prepare tomorrow\'s plan on paper',
  'Try a quiet body-scan meditation',
]

function fmt12h(t: string): string {
  try {
    const [h, m] = t.split(':').map(Number)
    return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h >= 12 ? 'PM' : 'AM'}`
  } catch { return t }
}

function fmtCountdown(secs: number): string {
  const s = Math.max(0, Math.floor(secs))
  const m = Math.floor(s / 60)
  const h = Math.floor(m / 60)
  if (h > 0) return `${h}:${String(m % 60).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
  return `${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}

export function ActiveSessionScreen({ prefs, session, sendCmd }: Props) {
  const [nudgeIdx, setNudgeIdx] = useState(0)
  const [showEnd, setShowEnd] = useState(false)

  useEffect(() => {
    const t = setInterval(() => setNudgeIdx((i) => (i + 1) % NUDGES.length), 45_000)
    return () => clearInterval(t)
  }, [])

  const minutes = Math.floor(session.timeRemaining / 60)

  return (
    <div className="size-full relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-orange-950 via-amber-950 to-slate-950" />

      {/* Ambient glow */}
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            'radial-gradient(circle at 30% 40%, rgba(251,146,60,0.22) 0%, transparent 50%), radial-gradient(circle at 70% 60%, rgba(245,158,11,0.18) 0%, transparent 50%)',
            'radial-gradient(circle at 70% 60%, rgba(251,146,60,0.22) 0%, transparent 50%), radial-gradient(circle at 30% 40%, rgba(245,158,11,0.18) 0%, transparent 50%)',
            'radial-gradient(circle at 30% 40%, rgba(251,146,60,0.22) 0%, transparent 50%), radial-gradient(circle at 70% 60%, rgba(245,158,11,0.18) 0%, transparent 50%)',
          ],
        }}
        transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
      />

      <div className="relative size-full flex flex-col items-center justify-between p-6">
        {/* Top bar */}
        <div className="w-full flex items-center justify-between">
          <div className="flex items-center gap-3">
            <UnwindLogo size={20} />
            <span className="text-sm text-orange-300/80" style={{ fontWeight: 400 }}>Unwinding</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-orange-950/40 border border-orange-800/30 text-orange-400/80" style={{ fontWeight: 400 }}>
              Docked
            </span>
          </div>
          <button
            onClick={() => setShowEnd(true)}
            className="p-2 rounded-full hover:bg-orange-900/30 transition-colors"
          >
            <X className="w-5 h-5 text-orange-400/60" />
          </button>
        </div>

        {/* Centre — breathing orb + timer */}
        <div className="flex-1 flex flex-col items-center justify-center gap-8">
          {/* Breathing orb */}
          <div className="relative w-36 h-36 flex items-center justify-center">
            <motion.div
              animate={{ scale: [1, 1.35, 1], opacity: [0.3, 0.6, 0.3] }}
              transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute inset-0 rounded-full bg-gradient-to-br from-orange-400/40 to-amber-400/40"
              style={{ filter: 'blur(28px)' }}
            />
            <motion.div
              animate={{ scale: [1, 1.18, 1], rotate: [0, 6, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
              className="w-28 h-28 rounded-full bg-gradient-to-br from-orange-500/40 to-amber-500/40 backdrop-blur-sm"
            />
          </div>

          {/* Countdown */}
          <div className="text-center">
            <div className="text-xs tracking-widest uppercase text-orange-300/50 mb-3" style={{ fontWeight: 500 }}>
              Time remaining
            </div>
            <div className="text-6xl text-white tracking-wide tabular-nums" style={{ fontWeight: 250 }}>
              {fmtCountdown(session.timeRemaining)}
            </div>
            <div className="text-sm text-orange-300/60 mt-3" style={{ fontWeight: 350 }}>
              Bedtime: {fmt12h(prefs.bedtime)}
            </div>
            {session.pickupCount > 0 && (
              <div className="text-xs text-orange-400/40 mt-1" style={{ fontWeight: 350 }}>
                {session.pickupCount} pickup{session.pickupCount !== 1 ? 's' : ''}
              </div>
            )}
          </div>

          {/* Rotating nudge */}
          <AnimatePresence mode="wait">
            <motion.div
              key={nudgeIdx}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.5 }}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-orange-950/30 border border-orange-800/25"
            >
              <Sparkles className="w-3.5 h-3.5 text-orange-400/60 shrink-0" />
              <span className="text-sm text-orange-200/65" style={{ fontWeight: 350 }}>{NUDGES[nudgeIdx]}</span>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Simulate pickup (desktop testing) */}
        <button
          onClick={() => sendCmd({ cmd: 'pickup' })}
          className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white/5 border border-white/8 hover:bg-white/10 transition-colors"
        >
          <Phone className="w-4 h-4 text-gray-500" />
          <span className="text-xs text-gray-500">Simulate phone pickup</span>
        </button>
      </div>

      {/* End session confirmation */}
      <AnimatePresence>
        {showEnd && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center p-5 z-10"
            onClick={() => setShowEnd(false)}
          >
            <motion.div
              initial={{ scale: 0.92, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.92, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-gradient-to-b from-orange-950 to-slate-950 rounded-3xl p-6 w-full border border-orange-800/30"
            >
              <h2 className="text-xl text-white mb-2" style={{ fontWeight: 400 }}>End ritual early?</h2>
              <p className="text-orange-200/65 text-sm mb-6" style={{ fontWeight: 350 }}>
                You still have {minutes} minute{minutes !== 1 ? 's' : ''} remaining.
              </p>
              <div className="space-y-2.5">
                <button
                  onClick={() => sendCmd({ cmd: 'stop_session' })}
                  className="w-full py-3.5 rounded-2xl bg-orange-600 hover:bg-orange-500 text-white transition-colors"
                  style={{ fontWeight: 500 }}
                >
                  End ritual
                </button>
                <button
                  onClick={() => setShowEnd(false)}
                  className="w-full py-2.5 text-orange-300/70 hover:text-orange-200 transition-colors text-sm"
                  style={{ fontWeight: 400 }}
                >
                  Continue unwinding
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
