import { motion } from 'motion/react'
import { AlertTriangle, Phone } from 'lucide-react'
import type { Prefs, SessionState, SendCmd } from '../App'

type Props = { prefs: Prefs; session: SessionState; sendCmd: SendCmd }

function fmt12h(t: string): string {
  try {
    const [h, m] = t.split(':').map(Number)
    return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h >= 12 ? 'PM' : 'AM'}`
  } catch { return t }
}

function fmtCost(secs: number): string {
  const s = Math.floor(secs)
  const m = Math.floor(s / 60)
  return `${m}:${String(s % 60).padStart(2, '0')}`
}

export function PausedScreen({ prefs, session, sendCmd }: Props) {
  const costMins = Math.floor(session.pausedSecs / 60)

  return (
    <div className="size-full relative overflow-hidden">
      {/* Jarring warm-red pulsing background */}
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            'radial-gradient(circle at 50% 40%, rgba(220,60,30,0.7) 0%, rgba(60,10,5,1) 65%)',
            'radial-gradient(circle at 50% 40%, rgba(245,80,40,0.9) 0%, rgba(60,10,5,1) 65%)',
            'radial-gradient(circle at 50% 40%, rgba(220,60,30,0.7) 0%, rgba(60,10,5,1) 65%)',
          ],
        }}
        transition={{ duration: 1.3, repeat: Infinity }}
      />

      <div className="relative size-full flex flex-col items-center justify-between p-7">
        {/* Status */}
        <div className="w-full text-center">
          <span className="text-xs tracking-widest uppercase text-red-400/80" style={{ fontWeight: 500 }}>
            Session paused
          </span>
        </div>

        {/* Centre content */}
        <div className="flex-1 flex flex-col items-center justify-center gap-6">
          {/* Pulsing icon */}
          <motion.div
            animate={{ scale: [1, 1.18, 1] }}
            transition={{ duration: 1.3, repeat: Infinity }}
            className="w-24 h-24 rounded-full bg-red-600/25 border-2 border-red-500/60 flex items-center justify-center"
          >
            <Phone className="w-10 h-10 text-red-300" />
          </motion.div>

          {/* Headline */}
          <div className="text-center">
            <h1 className="text-4xl text-white mb-1" style={{ fontWeight: 400 }}>Scrolling?</h1>
            <p className="text-red-200/60 text-sm" style={{ fontWeight: 350 }}>Every minute counts</p>
          </div>

          {/* Sleep cost counter */}
          <div className="text-center">
            <div className="text-xs tracking-widest uppercase text-red-400/60 mb-2" style={{ fontWeight: 500 }}>
              Sleep time lost
            </div>
            <div className="text-6xl text-red-300 tabular-nums" style={{ fontWeight: 300 }}>
              {fmtCost(session.pausedSecs)}
            </div>
            <div className="text-sm text-red-200/50 mt-2" style={{ fontWeight: 350 }}>
              of sleep replaced by screen time
            </div>
          </div>

          {/* Warning badge */}
          {costMins >= 1 && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-900/30 border border-red-700/30"
            >
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
              <span className="text-sm text-red-200/80" style={{ fontWeight: 400 }}>
                {costMins} min{costMins !== 1 ? 's' : ''} of sleep lost
              </span>
            </motion.div>
          )}

          <p className="text-orange-200/50 text-sm text-center max-w-xs" style={{ fontWeight: 350 }}>
            Bedtime {fmt12h(prefs.bedtime)} · Wake {fmt12h(prefs.wakeTime)}
          </p>
        </div>

        {/* Actions */}
        <div className="w-full space-y-3">
          <button
            onClick={() => sendCmd({ cmd: 'dock' })}
            className="w-full py-4 rounded-2xl bg-orange-600 hover:bg-orange-500 text-white text-lg transition-colors"
            style={{ fontWeight: 500 }}
          >
            Dock phone & continue
          </button>
          <button
            onClick={() => sendCmd({ cmd: 'stop_session' })}
            className="w-full py-3 rounded-2xl bg-white/5 border border-white/10 text-orange-200/60 hover:text-orange-100 transition-colors text-sm"
            style={{ fontWeight: 400 }}
          >
            End session &amp; sleep
          </button>
        </div>
      </div>
    </div>
  )
}
