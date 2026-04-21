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
      {/* Warm-red pulsing background */}
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            'radial-gradient(circle at 50% 40%, rgba(160,35,15,0.30) 0%, rgba(15,10,10,1) 65%)',
            'radial-gradient(circle at 50% 40%, rgba(175,42,18,0.42) 0%, rgba(15,10,10,1) 65%)',
            'radial-gradient(circle at 50% 40%, rgba(160,35,15,0.30) 0%, rgba(15,10,10,1) 65%)',
          ],
        }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
      />

      <div className="relative size-full flex flex-col items-center justify-between p-7">
        {/* Status */}
        <div className="w-full text-center">
          <span className="text-sm tracking-widest uppercase text-rose-300/85" style={{ fontWeight: 500 }}>
            Session paused
          </span>
        </div>

        {/* Centre content */}
        <div className="flex-1 flex flex-col items-center justify-center gap-6">
          {/* Pulsing icon */}
          <motion.div
            animate={{ scale: [1, 1.07, 1] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            className="w-20 h-20 rounded-full bg-rose-950/40 border border-rose-800/35 flex items-center justify-center"
          >
            <Phone className="w-9 h-9 text-rose-300/65" />
          </motion.div>

          {/* Headline */}
          <div className="text-center">
            <h1 className="text-3xl text-white mb-1" style={{ fontWeight: 400 }}>Scrolling?</h1>
            <p className="text-rose-200/75 text-base" style={{ fontWeight: 400 }}>Every minute counts</p>
          </div>

          {/* Sleep cost counter */}
          <div className="text-center">
            <div className="text-sm tracking-widest uppercase text-rose-300/75 mb-2" style={{ fontWeight: 500 }}>
              Sleep time lost
            </div>
            <div className="text-5xl text-rose-200 tabular-nums" style={{ fontWeight: 300 }}>
              {fmtCost(session.pausedSecs)}
            </div>
            <div className="text-sm text-rose-200/65 mt-2" style={{ fontWeight: 400 }}>
              of sleep replaced by screen time
            </div>
          </div>

          {/* Warning badge */}
          {costMins >= 1 && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-950/40 border border-rose-800/30"
            >
              <AlertTriangle className="w-4 h-4 text-rose-400/80 shrink-0" />
              <span className="text-sm text-rose-100/70" style={{ fontWeight: 400 }}>
                {costMins} min{costMins !== 1 ? 's' : ''} of sleep lost
              </span>
            </motion.div>
          )}

          <p className="text-orange-200/70 text-sm text-center max-w-xs" style={{ fontWeight: 400 }}>
            Bedtime {fmt12h(prefs.bedtime)} · Wake {fmt12h(prefs.wakeTime)}
          </p>
        </div>

        {/* Actions */}
        <div className="w-full max-w-xs mx-auto space-y-3">
          <button
            onClick={() => sendCmd({ cmd: 'dock' })}
            className="w-full py-4 rounded-xl bg-orange-700/80 hover:bg-orange-700 text-orange-50 text-lg transition-colors"
            style={{ fontWeight: 500 }}
          >
            Dock phone & continue
          </button>
          <button
            onClick={() => sendCmd({ cmd: 'stop_session' })}
            className="w-full py-2.5 text-orange-300/55 hover:text-orange-200/80 transition-colors text-sm"
            style={{ fontWeight: 400 }}
          >
            End session &amp; sleep
          </button>
        </div>
      </div>
    </div>
  )
}
