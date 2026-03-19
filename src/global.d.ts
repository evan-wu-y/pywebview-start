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
        start_heavy_task: (task_name?: string) => Promise<{
          ok: boolean
          message: string
          status: string
        }>
        stop_heavy_task: () => Promise<{
          ok: boolean
          message: string
          status: string
        }>
        clear_task_log: () => Promise<{
          ok: boolean
          message: string
          status: string
        }>
      }
    }
  }
}

export {}
