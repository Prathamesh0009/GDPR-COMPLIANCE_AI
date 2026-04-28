import { ArrowRight, Globe } from 'lucide-react'
import { motion } from 'framer-motion'

import { useReducedMotion } from '@/hooks/useReducedMotion'

import Card from '@/components/shared/Card'

/**
 * Simple source → destination flow rows.
 * @param {{ flows: Array<{ source?: string, destination?: string, crosses_border?: boolean, destination_country?: string | null }> }} props
 */
export default function DataFlowDiagram({ flows }) {
  const reduceMotion = useReducedMotion()
  if (!flows?.length) return null

  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-slate-900 dark:text-slate-50">Data flow map</h3>
      <ul className="space-y-4">
        {flows.map((flow, i) => (
          <motion.li
            key={`${flow.source}-${flow.destination}-${i}`}
            initial={reduceMotion ? false : { opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: reduceMotion ? 0 : i * 0.05, duration: 0.35 }}
            className="flex flex-wrap items-center gap-3 text-sm"
          >
            <span className="rounded-lg border border-slate-200 bg-white px-3 py-2 font-medium text-slate-800 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-100">
              {flow.source || '—'}
            </span>
            <ArrowRight className="h-4 w-4 text-slate-400" aria-hidden />
            <span className="rounded-lg border border-slate-200 bg-white px-3 py-2 font-medium text-slate-800 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-100">
              {flow.destination || '—'}
            </span>
            {flow.crosses_border ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
                <Globe className="h-3 w-3" aria-hidden />
                {flow.destination_country || 'Cross-border'}
              </span>
            ) : null}
          </motion.li>
        ))}
      </ul>
    </Card>
  )
}
