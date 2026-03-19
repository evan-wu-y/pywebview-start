import { useCallback, useEffect, useState } from "react"

type PythonApi = NonNullable<Window["pywebview"]>["api"]

export function usePythonBridge() {
  const [isReady, setIsReady] = useState<boolean>(() => Boolean(window.pywebview))

  useEffect(() => {
    if (window.pywebview) {
      setIsReady(true)
      return
    }

    const onReady = () => setIsReady(true)
    window.addEventListener("pywebviewready", onReady)
    return () => window.removeEventListener("pywebviewready", onReady)
  }, [])

  const callApi = useCallback(
    async <TMethod extends keyof PythonApi>(
      method: TMethod,
      ...args: Parameters<PythonApi[TMethod]>
    ): Promise<Awaited<ReturnType<PythonApi[TMethod]>>> => {
      const api = window.pywebview?.api
      if (!api || typeof api[method] !== "function") {
        throw new Error(`Python API "${String(method)}" is not available`)
      }

      const fn = api[method] as (...params: unknown[]) => unknown
      return (await fn(...args)) as Awaited<ReturnType<PythonApi[TMethod]>>
    },
    [],
  )

  return { isReady, callApi }
}

export function usePythonState<T = unknown>(propName: string) {
  const [propValue, setPropValue] = useState<T | undefined>(undefined)

  useEffect(() => {
    let removeStateListener: (() => void) | undefined

    const subscribeToState = () => {
      const state = (window.pywebview as { state?: Window["pywebview"] extends infer P ? P extends { state: infer S } ? S : unknown : unknown } | undefined)?.state as
        | (Record<string, unknown> & {
            addEventListener?: (type: "change", listener: (event: Event) => void) => void
            removeEventListener?: (type: "change", listener: (event: Event) => void) => void
          })
        | undefined
      if (!state || typeof state.addEventListener !== "function") return

      const handler = (event: Event) => {
        const detail = (event as CustomEvent<{ key: string; value: unknown }>).detail
        if (!detail || detail.key !== propName) return
        setPropValue(detail.value as T)
      }

      state.addEventListener("change", handler)

      // If value already exists, initialize immediately.
      const initialValue = (state as Record<string, unknown>)[propName]
      if (typeof initialValue !== "undefined") {
        setPropValue(initialValue as T)
      }

      removeStateListener = () => {
        if (typeof state.removeEventListener === "function") {
          state.removeEventListener("change", handler)
        }
      }
    }

    if (window.pywebview) {
      subscribeToState()
    } else {
      window.addEventListener("pywebviewready", subscribeToState, { once: true })
    }

    return () => {
      window.removeEventListener("pywebviewready", subscribeToState)
      removeStateListener?.()
    }
  }, [propName])

  return propValue
}
