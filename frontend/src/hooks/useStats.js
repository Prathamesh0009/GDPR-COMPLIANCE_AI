import { useCallback, useEffect, useState } from 'react'

import { getStats } from '@/api/client'

/** Fetch aggregate stats (optional; used when Stats page is wired). */
export function useStats() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getStats()
      setData(res.data)
    } catch (e) {
      setError(e)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const id = window.setTimeout(() => {
      void refetch()
    }, 0)
    return () => window.clearTimeout(id)
  }, [refetch])

  return { data, loading, error, refetch }
}
