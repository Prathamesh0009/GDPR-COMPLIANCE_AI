import { cn } from '@/lib/utils'

/**
 * Monospace pill for legal article references.
 * @param {{ label: string, className?: string }} props
 */
export default function ArticleTag({ label, className }) {
  return (
    <span
      className={cn(
        'inline-flex rounded-md bg-indigo-500/10 px-2 py-0.5 font-mono text-xs text-indigo-600 dark:text-indigo-400',
        className
      )}
    >
      {label}
    </span>
  )
}
