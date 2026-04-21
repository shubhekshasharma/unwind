import { motion } from 'motion/react'
import { Phone } from 'lucide-react'
import type { Prefs, SessionState, SendCmd } from '../App'

type Props = { prefs: Prefs; session: SessionState; sendCmd: SendCmd }

function sleepWindowMins(bedtime: string, wakeTime: string): number {
  const [bh, bm] = bedtime.split(':').map(Number)
  const [wh, wm] = wakeTime.split(':').map(Number)
  const bed = bh * 60 + bm
  const wake = wh * 60 + wm
  return wake > bed ? wake - bed : 1440 - bed + wake
}

function fmtWindow(mins: number): string {
  const m = Math.max(0, mins)
  const h = Math.floor(m / 60)
  const rem = m % 60
  return h > 0 ? `${h}h ${rem}m` : `${rem}m`
}

export function PausedScreen({ prefs, session, sendCmd }: Props) {
  const totalMins = sleepWindowMins(prefs.bedtime, prefs.wakeTime)
  const lostMins = Math.floor(session.pausedSecs / 60)
  const remainingMins = Math.max(0, totalMins - lostMins)
  const barPct = totalMins > 0 ? (remainingMins / totalMins) * 100 : 0

  return (
    <div className="size-full relative overflow-hidden">
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
          {session.pickupCount > 0 && (
            <span className="ml-3 text-xs text-rose-400/55" style={{ fontWeight: 400 }}>
              {session.pickupCount} pickup{session.pickupCount !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Centre */}
        <div className="flex-1 flex flex-col items-center justify-center gap-7 w-full max-w-xs mx-auto">
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

          {/* Dock warning callout — non-interactive */}
          <div className="w-full rounded-2xl bg-rose-950/35 border border-rose-700/30 px-5 py-4 flex items-center gap-3">
            <Phone className="w-5 h-5 text-rose-400/75 shrink-0" />
            <span className="text-sm text-rose-100/80 leading-snug" style={{ fontWeight: 400 }}>
              Place your phone back on the dock to resume
            </span>
          </div>

          {/* Sleep window bar */}
          <div className="w-full">
            <div className="text-xs tracking-widest uppercase text-rose-300/60 mb-3" style={{ fontWeight: 500 }}>
              Sleep window tonight
            </div>
            <div className="w-full h-3 rounded-full bg-rose-950/50 border border-rose-900/40 overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-rose-500/70 to-orange-400/60"
                animate={{ width: `${barPct}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
              />
            </div>
            <div className="mt-3 text-3xl text-rose-100 tabular-nums" style={{ fontWeight: 300 }}>
              {fmtWindow(remainingMins)}
            </div>
            <div className="text-xs text-rose-300/50 mt-1" style={{ fontWeight: 400 }}>
              available if you sleep now
            </div>
          </div>
        </div>

        {/* End session link */}
        <button
          onClick={() => sendCmd({ cmd: 'stop_session' })}
          className="w-full max-w-xs py-3 text-rose-300/50 hover:text-rose-200/80 transition-colors text-sm"
          style={{ fontWeight: 400 }}
        >
          End session &amp; sleep
        </button>
      </div>
    </div>
  )
}
