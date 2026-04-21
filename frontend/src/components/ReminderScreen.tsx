import { useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Bell, Smartphone, SlidersHorizontal } from 'lucide-react'
import { UnwindLogo } from './UnwindLogo'
import type { Prefs, SendCmd } from '../App'

type Props = { isPulsing: boolean; prefs: Prefs; sendCmd: SendCmd }

function fmt12h(t: string): string {
  try {
    const [h, m] = t.split(':').map(Number)
    return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h >= 12 ? 'PM' : 'AM'}`
  } catch { return t }
}

export function ReminderScreen({ isPulsing, prefs, sendCmd }: Props) {
  const [phoneDocked, setPhoneDocked] = useState(false)
  const [showDebug, setShowDebug] = useState(false)

  return (
    <div className="size-full relative overflow-hidden">
      {/* Background */}
      <motion.div
        className="absolute inset-0"
        animate={{
          background: isPulsing
            ? [
                'radial-gradient(circle at 50% 50%, rgba(251,146,60,0.18) 0%, rgba(249,115,22,0.10) 40%, rgba(15,23,42,1) 70%)',
                'radial-gradient(circle at 50% 50%, rgba(251,146,60,0.28) 0%, rgba(249,115,22,0.16) 40%, rgba(15,23,42,1) 70%)',
                'radial-gradient(circle at 50% 50%, rgba(251,146,60,0.18) 0%, rgba(249,115,22,0.10) 40%, rgba(15,23,42,1) 70%)',
              ]
            : 'radial-gradient(circle at 50% 50%, rgba(251,146,60,0.10) 0%, rgba(15,23,42,1) 70%)',
        }}
        transition={isPulsing ? { duration: 3, repeat: Infinity } : {}}
      />

      <div className="relative size-full flex flex-col items-center justify-between p-6">
        {/* Top bar */}
        <div className="w-full flex items-center justify-between">
          <div className="flex items-center gap-2">
            <UnwindLogo size={20} />
            <span className="text-sm text-orange-300/80" style={{ fontWeight: 400 }}>Unwind</span>
          </div>
          {!isPulsing && (
            <button
              onClick={() => sendCmd({ cmd: 'navigate', screen: 'home' })}
              className="text-xs text-orange-400/60 hover:text-orange-300 transition-colors px-3 py-1.5 rounded-full bg-orange-950/30 border border-orange-800/20"
            >
              Dismiss
            </button>
          )}
        </div>

        {/* Centre */}
        <div className="flex-1 flex flex-col items-center justify-center space-y-8">
          {isPulsing ? (
            <>
              {/* Soft ambient glow */}
              <motion.div
                animate={{ scale: [1, 1.2, 1], opacity: [0.12, 0.22, 0.12] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                className="w-52 h-52 rounded-full bg-gradient-to-br from-orange-400 to-amber-400 absolute"
                style={{ filter: 'blur(90px)' }}
              />

              <motion.div
                animate={{ scale: [1, 1.06, 1] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                className="relative"
              >
                <UnwindLogo size={88} animate />
              </motion.div>

              <div className="text-center space-y-3 relative">
                <h1 className="text-4xl text-white" style={{ fontWeight: 400 }}>
                  Time to unwind
                </h1>
                <p className="text-orange-100/80 text-base max-w-xs" style={{ fontWeight: 400 }}>
                  Dock your phone to begin your {prefs.unwindDuration}-minute ritual
                </p>
                <p className="text-orange-200/60 text-sm" style={{ fontWeight: 400 }}>
                  Bedtime: {fmt12h(prefs.bedtime)}
                </p>
              </div>
            </>
          ) : (
            <>
              <motion.div
                animate={{ scale: [1, 1.15, 1], opacity: [0.6, 1, 0.6] }}
                transition={{ duration: 2.5, repeat: Infinity }}
              >
                <Bell className="w-20 h-20 text-orange-400/75" />
              </motion.div>
              <div className="text-center space-y-3">
                <h1 className="text-2xl text-white" style={{ fontWeight: 400 }}>Get ready to unwind</h1>
                <p className="text-orange-200/80 text-base max-w-xs" style={{ fontWeight: 400 }}>
                  Your {prefs.unwindDuration}-minute ritual starts in 5 minutes
                </p>
                <p className="text-orange-300/70 text-sm" style={{ fontWeight: 400 }}>
                  Bedtime: {fmt12h(prefs.bedtime)}
                </p>
              </div>
            </>
          )}
        </div>

        {/* Actions */}
        <div className="w-full space-y-3 max-w-sm">
          {isPulsing ? (
            <>
              <button
                onClick={() => sendCmd({ cmd: 'start_session' })}
                className="w-full py-4 rounded-2xl text-lg bg-orange-700/80 hover:bg-orange-700 text-orange-50 transition-colors"
                style={{ fontWeight: 500 }}
              >
                Start Unwind
              </button>

              <button
                onClick={() => sendCmd({ cmd: 'skip' })}
                className="w-full py-2.5 text-sm text-orange-400/50 hover:text-orange-300/70 transition-colors"
                style={{ fontWeight: 400 }}
              >
                Not tonight
              </button>
            </>
          ) : (
            <button
              onClick={() => sendCmd({ cmd: 'navigate', screen: 'home' })}
              className="w-full py-3.5 rounded-2xl bg-orange-950/25 border border-orange-800/20 text-orange-300/70 hover:bg-orange-950/40 transition-colors"
              style={{ fontWeight: 400 }}
            >
              Got it, I'll be ready
            </button>
          )}
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
                onClick={() => { setPhoneDocked(d => !d); setShowDebug(false) }}
                className="w-full text-left text-sm text-slate-300 hover:text-white px-2 py-1.5 rounded-lg hover:bg-white/5 transition-colors flex items-center gap-2"
              >
                <Smartphone className="w-3.5 h-3.5 shrink-0" />
                {phoneDocked ? 'Undock phone' : 'Dock phone'}
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
