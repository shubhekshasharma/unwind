import { motion } from 'motion/react'

type UnwindLogoProps = {
  size?: number
  animate?: boolean
}

export function UnwindLogo({ size = 32, animate = false }: UnwindLogoProps) {
  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      animate={animate ? { rotate: [0, -5, 5, 0] } : {}}
      transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
    >
      <path
        d="M4 24 C10 20, 30 20, 36 24"
        stroke="url(#g1)"
        strokeWidth="1.5"
        strokeLinecap="round"
        fill="none"
      />
      <motion.circle
        cx="20" cy="16" r="8"
        fill="url(#g2)"
        animate={animate ? { scale: [1, 1.05, 1], opacity: [0.9, 1, 0.9] } : {}}
        transition={{ duration: 4, repeat: Infinity }}
      />
      <motion.circle
        cx="20" cy="16" r="10"
        fill="url(#g3)"
        opacity="0.3"
        animate={animate ? { scale: [1, 1.15, 1], opacity: [0.2, 0.4, 0.2] } : {}}
        transition={{ duration: 4, repeat: Infinity }}
      />
      <defs>
        <linearGradient id="g1" x1="4" y1="24" x2="36" y2="24">
          <stop offset="0%" stopColor="#fb923c" stopOpacity="0.4" />
          <stop offset="50%" stopColor="#f59e0b" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#fb923c" stopOpacity="0.4" />
        </linearGradient>
        <linearGradient id="g2" x1="20" y1="8" x2="20" y2="24">
          <stop offset="0%" stopColor="#fbbf24" />
          <stop offset="100%" stopColor="#f97316" />
        </linearGradient>
        <radialGradient id="g3">
          <stop offset="0%" stopColor="#fb923c" />
          <stop offset="100%" stopColor="#f97316" stopOpacity="0" />
        </radialGradient>
      </defs>
    </motion.svg>
  )
}
