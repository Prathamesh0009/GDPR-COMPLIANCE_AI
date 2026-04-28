import { memo, useMemo } from 'react'
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
import { useReducedMotion } from '@/hooks/useReducedMotion'
import { useChartColors } from '@/lib/chartTheme'

/**
 * Vertical bar chart of relative article emphasis (mention count / max).
 * @param {{ findings: Array<{ relevant_articles?: string[] }> }} props
 */
function ConfidenceChart({ findings }) {
  const reduceMotion = useReducedMotion()
  const c = useChartColors()
  const data = useMemo(() => {
    const counts = {}
    for (const f of findings || []) {
      for (const a of f.relevant_articles || []) {
        counts[a] = (counts[a] || 0) + 1
      }
    }
    const max = Math.max(...Object.values(counts), 1)
    return Object.entries(counts)
      .map(([article, n]) => ({
        article,
        weight: n / max,
      }))
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 16)
  }, [findings])

  if (!data.length) return null

  const tooltipStyle = {
    background: c.tooltipBg,
    border: `1px solid ${c.tooltipBorder}`,
    borderRadius: '0.5rem',
  }

  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-slate-900 dark:text-slate-50">
        Article emphasis (relative)
      </h3>
      <div className="h-72 w-full" role="img" aria-label="Relative article emphasis bar chart">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ left: 8, right: 16, top: 8, bottom: 8 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={c.grid}
              strokeOpacity={0.45}
              horizontal={false}
            />
            <XAxis
              type="number"
              domain={[0, 1]}
              tick={{ fill: c.axis, fontSize: 11 }}
              tickFormatter={(v) => `${Math.round(v * 100)}%`}
            />
            <YAxis
              type="category"
              dataKey="article"
              width={120}
              tick={{
                fill: c.axis,
                fontSize: 10,
                fontFamily: 'JetBrains Mono, monospace',
              }}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              labelStyle={{ color: c.tooltipMuted, fontSize: 12 }}
            />
            <Bar
              dataKey="weight"
              fill={c.primary}
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

export default memo(ConfidenceChart)
