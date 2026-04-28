import { motion, useReducedMotion } from 'framer-motion'

import { severityConfig } from '@/lib/theme'
import { cn } from '@/lib/utils'

/**
 * Violation severity or compliance risk level pill with optional pulse.
 * @param {{ level: string, className?: string }} props
 */
export default function SeverityBadge({ level, className }) {
  const key = String(level || 'unknown').toLowerCase()
  const conf = severityConfig[key] ?? severityConfig.unknown
  const reduceMotion = useReducedMotion()
  const pulse = conf.pulse && !reduceMotion

  const inner = (
    <span
      className={cn(
        'inline-flex rounded-full px-3 py-1 text-xs font-medium',
        conf.bg,
        conf.color,
        className
      )}
    >
      {conf.label}
    </span>
  )

  if (!pulse) return inner

  return (
    <motion.span
      animate={{ opacity: [0.7, 1], scale: [0.97, 1] }}
      transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      className="inline-flex"
    >
      {inner}
    </motion.span>
  )
}
