import { useCallback, useEffect, useState } from 'react'

import { getHistory } from '@/api/client'

/**
 * Fetch analysis history (optional; used when History page is wired).
 * @param {{ limit?: number, mode?: string }} [options]
 */
export function useHistory(options = {}) {
  const { limit = 50, mode } = options
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getHistory({ limit, ...(mode ? { mode } : {}) })
      setData(res.data)
    } catch (e) {
      setError(e)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [limit, mode])

  useEffect(() => {
    const id = window.setTimeout(() => {
      void refetch()
    }, 0)
    return () => window.clearTimeout(id)
  }, [refetch])

  return { data, loading, error, refetch }
}
