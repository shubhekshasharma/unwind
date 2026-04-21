import { useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Moon, Clock } from 'lucide-react'
import { UnwindLogo } from './UnwindLogo'
import type { Prefs, SendCmd } from '../App'

type Props = { prefs: Prefs; sendCmd: SendCmd }

const DURATIONS = [15, 30, 45, 60]

function formatUnwindStart(bedtime: string, duration: number): string {
  try {
    const [h, m] = bedtime.split(':').map(Number)
    const totalMins = h * 60 + m - duration
    const sh = Math.floor(((totalMins % 1440) + 1440) % 1440 / 60)
    const sm = ((totalMins % 1440) + 1440) % 1440 % 60
    const period = sh >= 12 ? 'PM' : 'AM'
    const h12 = sh % 12 || 12
    return `${h12}:${String(sm).padStart(2, '0')} ${period}`
  } catch {
    return ''
  }
}

export function OnboardingScreen({ prefs, sendCmd }: Props) {
  const [step, setStep] = useState(0)
  const [bedtime, setBedtime] = useState(prefs.bedtime)
  const [wakeTime, setWakeTime] = useState(prefs.wakeTime)
  const [duration, setDuration] = useState(prefs.unwindDuration)

  const handleComplete = () => {
    sendCmd({
      cmd: 'set_prefs',
      prefs: { bedtime, wakeTime, unwindDuration: duration, onboardingComplete: true },
    })
  }

  return (
    <div className="size-full relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-orange-950 via-amber-950 to-slate-950" />
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            'radial-gradient(circle at 50% 20%, rgba(251,146,60,0.2) 0%, transparent 50%)',
            'radial-gradient(circle at 50% 20%, rgba(251,146,60,0.12) 0%, transparent 50%)',
            'radial-gradient(circle at 50% 20%, rgba(251,146,60,0.2) 0%, transparent 50%)',
          ],
        }}
        transition={{ duration: 4, repeat: Infinity }}
      />

      <div className="relative size-full flex flex-col items-center justify-between p-6">
        {/* Progress dots */}
        <div className="flex gap-2 pt-4">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className={`h-2 rounded-full transition-all duration-300 ${
                i === step ? 'bg-orange-400 w-6' : i < step ? 'bg-orange-600/60 w-2' : 'bg-orange-900/50 w-2'
              }`}
            />
          ))}
        </div>

        {/* Step content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -16 }}
            transition={{ duration: 0.35 }}
            className="flex-1 flex flex-col items-center justify-center w-full max-w-sm"
          >
            {step === 0 && (
              <div className="text-center space-y-6">
                <UnwindLogo size={88} animate />
                <div>
                  <h1 className="text-3xl text-white mb-3" style={{ fontWeight: 400 }}>
                    Welcome to Unwind
                  </h1>
                  <p className="text-orange-200/80 text-base leading-relaxed" style={{ fontWeight: 400 }}>
                    Create a calming bedtime ritual that helps you put down your phone and drift into restful sleep.
                  </p>
                </div>
              </div>
            )}

            {step === 1 && (
              <div className="w-full space-y-8">
                <div className="text-center">
                  <Moon className="w-14 h-14 text-orange-400 mx-auto mb-4 opacity-90" />
                  <h2 className="text-2xl text-white mb-2" style={{ fontWeight: 400 }}>
                    Set your sleep schedule
                  </h2>
                  <p className="text-orange-200/75 text-base" style={{ fontWeight: 400 }}>
                    When do you want to sleep and wake up?
                  </p>
                </div>
                <div className="space-y-5">
                  <div className="space-y-2">
                    <label className="text-sm text-orange-200/80" style={{ fontWeight: 500 }}>Bedtime</label>
                    <input
                      type="time"
                      value={bedtime}
                      onChange={(e) => setBedtime(e.target.value)}
                      className="w-full px-4 py-3.5 rounded-2xl bg-orange-950/30 border border-orange-800/30 text-white text-lg focus:outline-none focus:border-orange-600/60 transition-colors"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-orange-200/80" style={{ fontWeight: 500 }}>Wake time</label>
                    <input
                      type="time"
                      value={wakeTime}
                      onChange={(e) => setWakeTime(e.target.value)}
                      className="w-full px-4 py-3.5 rounded-2xl bg-orange-950/30 border border-orange-800/30 text-white text-lg focus:outline-none focus:border-orange-600/60 transition-colors"
                    />
                  </div>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="w-full space-y-7">
                <div className="text-center">
                  <Clock className="w-14 h-14 text-orange-400 mx-auto mb-4 opacity-90" />
                  <h2 className="text-2xl text-white mb-2" style={{ fontWeight: 400 }}>
                    Ritual duration
                  </h2>
                  <p className="text-orange-200/75 text-base" style={{ fontWeight: 400 }}>
                    How long should your wind-down ritual be?
                  </p>
                </div>
                <div className="space-y-3">
                  {DURATIONS.map((d) => (
                    <button
                      key={d}
                      onClick={() => setDuration(d)}
                      className={`w-full px-6 py-4 rounded-2xl border-2 transition-all ${
                        duration === d
                          ? 'bg-orange-600/25 border-orange-500/80 text-white'
                          : 'bg-orange-950/20 border-orange-900/30 text-orange-200/80 hover:border-orange-800/60'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-lg" style={{ fontWeight: 400 }}>{d} minutes</span>
                        {d === 30 && (
                          <span className="text-xs text-orange-400/80 px-2 py-0.5 rounded-full bg-orange-900/30" style={{ fontWeight: 400 }}>
                            Recommended
                          </span>
                        )}
                      </div>
                      {duration === d && bedtime && (
                        <div className="text-sm text-orange-400/80 mt-1 text-left" style={{ fontWeight: 400 }}>
                          Starts at {formatUnwindStart(bedtime, d)}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="w-full max-w-sm space-y-3">
          {step < 2 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="w-full py-3.5 rounded-2xl bg-orange-600 hover:bg-orange-500 text-white transition-colors"
              style={{ fontWeight: 500 }}
            >
              Continue
            </button>
          ) : (
            <button
              onClick={handleComplete}
              className="w-full py-3.5 rounded-2xl bg-orange-600 hover:bg-orange-500 text-white transition-colors"
              style={{ fontWeight: 500 }}
            >
              Start Unwinding
            </button>
          )}
          {step > 0 && (
            <button
              onClick={() => setStep(step - 1)}
              className="w-full py-2 text-orange-300/70 hover:text-orange-200 transition-colors text-sm"
              style={{ fontWeight: 400 }}
            >
              Back
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
