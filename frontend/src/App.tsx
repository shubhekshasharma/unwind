import { useEffect, useRef, useState, useCallback } from 'react'
import { OnboardingScreen } from './components/OnboardingScreen'
import { HomeScreen } from './components/HomeScreen'
import { ReminderScreen } from './components/ReminderScreen'
import { ActiveSessionScreen } from './components/ActiveSessionScreen'
import { PausedScreen } from './components/PausedScreen'
import { IncompleteScreen } from './components/IncompleteScreen'
import { CompletionScreen } from './components/CompletionScreen'
import { StatsScreen } from './components/StatsScreen'

export type Screen =
  | 'onboarding'
  | 'home'
  | 'reminder'
  | 'reminderPulse'
  | 'session'
  | 'paused'
  | 'incomplete'
  | 'complete'
  | 'stats'

export type Prefs = {
  bedtime: string
  wakeTime: string
  unwindDuration: number
  onboardingComplete: boolean
}

export type SessionState = {
  timeRemaining: number
  elapsed: number
  pickupCount: number
  isPhoneDocked: boolean
  isRunning: boolean
  pausedSecs: number
}

type AppState = {
  screen: Screen
  session: SessionState
  prefs: Prefs
}

const DEFAULT_STATE: AppState = {
  screen: 'onboarding',
  session: {
    timeRemaining: 0,
    elapsed: 0,
    pickupCount: 0,
    isPhoneDocked: true,
    isRunning: false,
    pausedSecs: 0,
  },
  prefs: {
    bedtime: '23:00',
    wakeTime: '07:00',
    unwindDuration: 30,
    onboardingComplete: false,
  },
}

export type SendCmd = (payload: Record<string, unknown>) => void

export default function App() {
  const [appState, setAppState] = useState<AppState>(DEFAULT_STATE)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current)
        reconnectTimer.current = null
      }
    }

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as AppState
        setAppState(data)
      } catch {
        // ignore malformed message
      }
    }

    ws.onclose = () => {
      setConnected(false)
      reconnectTimer.current = setTimeout(connect, 2000)
    }

    ws.onerror = () => ws.close()
  }, [])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }
  }, [connect])

  const sendCmd: SendCmd = useCallback((payload) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload))
    }
  }, [])

  const { screen, session, prefs } = appState

  return (
    <div className="size-full relative overflow-hidden bg-slate-950" style={{ height: '100dvh' }}>
      {!connected && (
        <div className="absolute top-0 inset-x-0 z-50 flex justify-center py-2">
          <div className="text-xs text-orange-400/70 px-3 py-1 rounded-full bg-orange-950/40 border border-orange-800/20">
            Reconnecting…
          </div>
        </div>
      )}

      {screen === 'onboarding' && (
        <OnboardingScreen prefs={prefs} sendCmd={sendCmd} />
      )}
      {screen === 'home' && (
        <HomeScreen prefs={prefs} session={session} sendCmd={sendCmd} />
      )}
      {screen === 'reminder' && (
        <ReminderScreen isPulsing={false} prefs={prefs} session={session} sendCmd={sendCmd} />
      )}
      {screen === 'reminderPulse' && (
        <ReminderScreen isPulsing={true} prefs={prefs} session={session} sendCmd={sendCmd} />
      )}
      {screen === 'session' && (
        <ActiveSessionScreen prefs={prefs} session={session} sendCmd={sendCmd} />
      )}
      {screen === 'paused' && (
        <PausedScreen prefs={prefs} session={session} sendCmd={sendCmd} />
      )}
      {screen === 'incomplete' && (
        <IncompleteScreen prefs={prefs} session={session} sendCmd={sendCmd} />
      )}
      {screen === 'complete' && (
        <CompletionScreen prefs={prefs} session={session} sendCmd={sendCmd} />
      )}
      {screen === 'stats' && (
        <StatsScreen prefs={prefs} sendCmd={sendCmd} />
      )}
    </div>
  )
}
