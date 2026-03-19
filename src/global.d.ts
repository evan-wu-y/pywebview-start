declare global {
  type PywebviewStateChangeDetail = {
    key: string
    value: unknown
  }

  type PywebviewState = Record<string, unknown> & {
    addEventListener: (
      type: "change",
      listener: (event: CustomEvent<PywebviewStateChangeDetail>) => void,
    ) => void
    removeEventListener?: (
      type: "change",
      listener: (event: CustomEvent<PywebviewStateChangeDetail>) => void,
    ) => void
  }

  interface Window {
    pywebview?: {
      state: PywebviewState
      api: {
        run_basic_task: (task?: string) => Promise<{
          task: string
          message: string
          now: string
          platform: string
          python_version: string
        }>
      }
    }
  }
}

export {}
