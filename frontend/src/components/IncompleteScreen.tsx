import { motion } from 'motion/react'
import { Moon } from 'lucide-react'
import type { Prefs, SessionState, SendCmd } from '../App'

type Props = { prefs: Prefs; session: SessionState; sendCmd: SendCmd }

function fmt12h(t: string): string {
  try {
    const [h, m] = t.split(':').map(Number)
    return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h >= 12 ? 'PM' : 'AM'}`
  } catch { return t }
}

export function IncompleteScreen({ prefs, session, sendCmd }: Props) {
  const totalSecs = prefs.unwindDuration * 60
  const completedMins = Math.floor(session.elapsed / 60)
  const totalMins = prefs.unwindDuration
  const remainingMins = Math.max(0, totalMins - completedMins)
  const fraction = Math.min(1, totalSecs > 0 ? session.elapsed / totalSecs : 0)

  return (
    <div className="size-full relative overflow-hidden">
      <div className="absolute inset-0" style={{ background: '#2a1608' }} />
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            'radial-gradient(circle at 50% 30%, rgba(180,80,20,0.35) 0%, transparent 60%)',
            'radial-gradient(circle at 50% 30%, rgba(200,90,25,0.45) 0%, transparent 60%)',
            'radial-gradient(circle at 50% 30%, rgba(180,80,20,0.35) 0%, transparent 60%)',
          ],
        }}
        transition={{ duration: 4, repeat: Infinity }}
      />

      <div className="relative size-full flex flex-col items-center justify-between p-7">
        {/* Status */}
        <div className="w-full text-center">
          <span className="text-xs tracking-widest uppercase text-amber-500/70" style={{ fontWeight: 500 }}>
            Ritual incomplete
          </span>
        </div>

        {/* Centre */}
        <div className="flex-1 flex flex-col items-center justify-center gap-6 w-full">
          <h1 className="text-3xl text-white text-center" style={{ fontWeight: 400 }}>
            Bedtime has passed.
          </h1>

          {/* Progress display */}
          <div className="text-center">
            <div className="text-xl text-amber-200/80" style={{ fontWeight: 350 }}>
              You completed{' '}
              <span className="text-white" style={{ fontWeight: 500 }}>{completedMins}</span>
              {' '}of{' '}
              <span className="text-white" style={{ fontWeight: 500 }}>{totalMins}</span>
              {' '}minutes
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full rounded-full bg-white/10 h-2.5 overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-orange-600 to-amber-500"
              initial={{ width: 0 }}
              animate={{ width: `${fraction * 100}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          </div>

          {/* Sub message */}
          {remainingMins > 0 ? (
            <p className="text-orange-200/60 text-sm text-center max-w-xs" style={{ fontWeight: 350 }}>
              Continuing means {remainingMins} more minute{remainingMins !== 1 ? 's' : ''} past your{' '}
              {fmt12h(prefs.bedtime)} bedtime.
            </p>
          ) : (
            <p className="text-green-400/70 text-sm text-center" style={{ fontWeight: 350 }}>
              You completed the full ritual. Time to sleep!
            </p>
          )}

          <div className="flex items-center gap-2 text-orange-300/40">
            <Moon className="w-5 h-5" />
            <span className="text-sm" style={{ fontWeight: 350 }}>Wake time: {fmt12h(prefs.wakeTime)}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="w-full space-y-3">
          {remainingMins > 0 && (
            <button
              onClick={() => sendCmd({ cmd: 'continue_session' })}
              className="w-full py-4 rounded-2xl bg-orange-600 hover:bg-orange-500 text-white text-lg transition-colors"
              style={{ fontWeight: 500 }}
            >
              Continue ritual anyway
            </button>
          )}
          <button
            onClick={() => sendCmd({ cmd: 'stop_session' })}
            className={`w-full py-4 rounded-2xl transition-colors text-lg ${
              remainingMins === 0
                ? 'bg-orange-600 hover:bg-orange-500 text-white'
                : 'bg-white/5 border border-white/10 text-orange-200/70 hover:text-orange-100'
            }`}
            style={{ fontWeight: remainingMins === 0 ? 500 : 400 }}
          >
            End now &amp; sleep ☽
          </button>
        </div>
      </div>
    </div>
  )
}
