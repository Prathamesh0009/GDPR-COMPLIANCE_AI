import { useCallback, useEffect, useState } from 'react'

import { analyzeCompliance, analyzeViolation, getErrorMessage } from '@/api/client'
import { MODES } from '@/lib/constants'

/**
 * Run violation or compliance analysis with loading / elapsed / error state.
 */
export function useAnalyze() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [elapsedSec, setElapsedSec] = useState(0)
  const [completedAt, setCompletedAt] = useState(null)

  useEffect(() => {
    if (!loading) return undefined
    const t0 = Date.now()
    const id = window.setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - t0) / 1000))
    }, 1000)
    return () => window.clearInterval(id)
  }, [loading])

  const analyze = useCallback(async (mode, text) => {
    setElapsedSec(0)
    setLoading(true)
    setError(null)
    setResult(null)
    setCompletedAt(null)
    try {
      const response =
        mode === MODES.VIOLATION
          ? await analyzeViolation(text)
          : await analyzeCompliance(text)
      setResult(response.data)
      setCompletedAt(new Date().toISOString())
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  const clear = useCallback(() => {
    setResult(null)
    setError(null)
    setCompletedAt(null)
  }, [])

  return { result, loading, error, elapsedSec, completedAt, analyze, clear }
}
