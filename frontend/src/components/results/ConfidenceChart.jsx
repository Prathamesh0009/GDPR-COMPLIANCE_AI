import { useMemo } from 'react'
import { useReducedMotion } from 'framer-motion'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import Card from '@/components/shared/Card'

/**
 * Vertical bar chart of relative article emphasis (mention count / max).
 * @param {{ findings: Array<{ relevant_articles?: string[] }> }} props
 */
export default function ConfidenceChart({ findings }) {
  const reduceMotion = useReducedMotion()
  const data = useMemo(() => {
    const counts = {}
    for (const f of findings || []) {
      for (const a of f.relevant_articles || []) {
        counts[a] = (counts[a] || 0) + 1
      }
    }
    const max = Math.max(...Object.values(counts), 1)
    return Object.entries(counts)
      .map(([article, c]) => ({
        article,
        weight: c / max,
      }))
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 16)
  }, [findings])

  if (!data.length) return null

  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-slate-900 dark:text-slate-50">
        Article emphasis (relative)
      </h3>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ left: 8, right: 16, top: 8, bottom: 8 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgb(51 65 85)"
              strokeOpacity={0.35}
              horizontal={false}
            />
            <XAxis
              type="number"
              domain={[0, 1]}
              tick={{ fill: 'rgb(148 163 184)', fontSize: 11 }}
              tickFormatter={(v) => `${Math.round(v * 100)}%`}
            />
            <YAxis
              type="category"
              dataKey="article"
              width={120}
              tick={{ fill: 'rgb(148 163 184)', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}
            />
            <Tooltip
              contentStyle={{
                background: 'rgb(30 41 59)',
                border: '1px solid rgb(51 65 85)',
                borderRadius: '0.5rem',
              }}
              labelStyle={{ color: 'rgb(148 163 184)', fontSize: 12 }}
            />
            <Bar
              dataKey="weight"
              fill="rgb(99 102 241)"
              radius={[0, 4, 4, 0]}
              isAnimationActive={!reduceMotion}
              animationDuration={600}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
