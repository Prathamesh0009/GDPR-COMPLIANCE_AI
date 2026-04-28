/* eslint-disable react-refresh/only-export-components -- Provider + hook */
import { createContext, useCallback, useContext, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { AlertCircle, CheckCircle, Info } from 'lucide-react'

const ToastContext = createContext({
  /** @type {(opts: { type?: 'success' | 'error' | 'info', message: string }) => void} */
  showToast: () => {},
})

const styles = {
  success: 'border-emerald-500/30 text-emerald-400',
  error: 'border-rose-500/30 text-rose-400',
  info: 'border-indigo-500/30 text-indigo-400',
}

/**
 * @param {{ children: import('react').ReactNode }} props
 */
export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null)
  const reduceMotion = useReducedMotion()

  const showToast = useCallback(({ type = 'info', message }) => {
    const id = Date.now()
    setToast({ id, type, message })
    window.setTimeout(() => {
      setToast((t) => (t?.id === id ? null : t))
    }, 4000)
  }, [])

  const Icon = toast?.type === 'success' ? CheckCircle : toast?.type === 'error' ? AlertCircle : Info

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-50 max-w-sm">
        <AnimatePresence>
          {toast ? (
            <motion.div
              key={toast.id}
              initial={reduceMotion ? false : { x: 100, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={reduceMotion ? false : { x: 100, opacity: 0 }}
              transition={{ duration: reduceMotion ? 0 : 0.25 }}
              className={`pointer-events-auto flex gap-3 rounded-lg border bg-slate-800 p-4 shadow-lg dark:bg-slate-800 ${styles[toast.type] ?? styles.info}`}
            >
              <Icon className="h-5 w-5 shrink-0" aria-hidden />
              <p className="text-sm text-slate-100">{toast.message}</p>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}
