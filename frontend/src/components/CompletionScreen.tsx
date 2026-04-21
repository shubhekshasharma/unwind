import { motion } from 'motion/react'
import { Moon, Sun, Sparkles, CheckCircle2 } from 'lucide-react'
import type { Prefs, SessionState, SendCmd } from '../App'

type Props = { prefs: Prefs; session: SessionState; sendCmd: SendCmd }

function fmt12h(t: string): string {
  try {
    const [h, m] = t.split(':').map(Number)
    return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h >= 12 ? 'PM' : 'AM'}`
  } catch { return t }
}

function fmtDuration(secs: number): string {
  const m = Math.floor(secs / 60)
  const h = Math.floor(m / 60)
  if (h > 0) return `${h}h ${String(m % 60).padStart(2, '0')}m`
  return `${m}m`
}

export function CompletionScreen({ prefs, session, sendCmd }: Props) {
  const durationStr = fmtDuration(session.elapsed || prefs.unwindDuration * 60)
  const { pickupCount } = session

  return (
    <div className="size-full relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950" />
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            'radial-gradient(circle at 50% 30%, rgba(251,146,60,0.08) 0%, transparent 50%)',
            'radial-gradient(circle at 50% 30%, rgba(251,146,60,0.04) 0%, transparent 50%)',
            'radial-gradient(circle at 50% 30%, rgba(251,146,60,0.08) 0%, transparent 50%)',
          ],
        }}
        transition={{ duration: 6, repeat: Infinity }}
      />

      <div className="relative size-full flex flex-col items-center justify-between p-6">
        <div className="flex-1 flex flex-col items-center justify-center space-y-6">
          {/* Check badge */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', duration: 0.8 }}
            className="relative"
          >
            <motion.div
              animate={{ scale: [1, 1.2, 1], opacity: [0.25, 0.45, 0.25] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="absolute inset-0 rounded-full bg-gradient-to-br from-orange-500 to-amber-500"
              style={{ filter: 'blur(28px)' }}
            />
            <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-orange-600/25 to-amber-600/25 border-2 border-orange-500/35 flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-orange-400" />
            </div>
          </motion.div>

          {/* Heading */}
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-center space-y-2"
          >
            <h1 className="text-3xl text-white" style={{ fontWeight: 400 }}>Ritual complete</h1>
            <p className="text-orange-200/80 text-base max-w-xs" style={{ fontWeight: 400 }}>
              You've taken time to unwind. Your mind is ready for restful sleep.
            </p>
          </motion.div>

          {/* Stats card */}
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="w-full max-w-xs space-y-3"
          >
            <div className="bg-gradient-to-br from-orange-950/30 to-amber-950/25 rounded-2xl border border-orange-800/20 p-5">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-4 h-4 text-orange-400/80" />
                <span className="text-base text-orange-300/90" style={{ fontWeight: 500 }}>Tonight's session</span>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-base text-orange-200/80" style={{ fontWeight: 400 }}>Unwind time</span>
                  <span className="text-base text-white" style={{ fontWeight: 600 }}>{durationStr}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-base text-orange-200/80" style={{ fontWeight: 400 }}>Phone pickups</span>
                  <span className={`text-base ${pickupCount === 0 ? 'text-green-400' : 'text-orange-200'}`} style={{ fontWeight: 600 }}>
                    {pickupCount === 0 ? 'None ✓' : pickupCount}
                  </span>
                </div>
                <div className="h-px bg-orange-800/25" />
                <div className="flex justify-between items-center">
                  <span className="text-base text-orange-200/80" style={{ fontWeight: 400 }}>Bedtime</span>
                  <span className="text-base text-white" style={{ fontWeight: 600 }}>{fmt12h(prefs.bedtime)}</span>
                </div>
              </div>
            </div>

            {/* Wake time */}
            <div className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-amber-950/20 border border-amber-800/20">
              <Sun className="w-5 h-5 text-amber-400/90 shrink-0" />
              <div>
                <div className="text-base text-white" style={{ fontWeight: 500 }}>Wake: {fmt12h(prefs.wakeTime)}</div>
                <div className="text-sm text-amber-300/75" style={{ fontWeight: 400 }}>Good morning awaits</div>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="text-center space-y-1"
          >
            <Moon className="w-8 h-8 text-orange-400/40 mx-auto" />
            <p className="text-orange-200/60 text-sm" style={{ fontWeight: 400 }}>Sweet dreams</p>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="w-full max-w-xs space-y-2.5"
        >
          <button
            onClick={() => sendCmd({ cmd: 'navigate', screen: 'stats' })}
            className="w-full py-3.5 rounded-2xl bg-orange-950/25 border border-orange-800/20 text-orange-300/80 hover:text-orange-200 transition-colors text-base"
            style={{ fontWeight: 400 }}
          >
            View sleep history
          </button>
          <button
            onClick={() => sendCmd({ cmd: 'navigate', screen: 'home' })}
            className="w-full py-2.5 text-orange-300/55 hover:text-orange-200/80 transition-colors text-sm"
            style={{ fontWeight: 400 }}
          >
            Back to home
          </button>
        </motion.div>
      </div>
    </div>
  )
}
