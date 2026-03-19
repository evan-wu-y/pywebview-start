import { useState } from "react"
import { IconBolt, IconCircleCheckFilled, IconLoader2 } from "@tabler/icons-react"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { usePythonBridge, usePythonState } from "@/hooks/pythonBridge"

type BasicTaskResult = {
  task: string
  message: string
  now: string
  platform: string
  python_version: string
}

export function App() {
  const { isReady, callApi } = usePythonBridge()
  const [taskName, setTaskName] = useState("demo task")
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<BasicTaskResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const ticker = usePythonState<number>("ticker")

  const runTask = async () => {
    setError(null)
    setResult(null)
    setIsRunning(true)
    try {
      const response = await callApi("run_basic_task", taskName)
      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setIsRunning(false)
    }
  }

  const canRun = isReady && !isRunning

  return (
    <div className="min-h-svh bg-slate-50 p-4">
      <main className="mx-auto w-full max-w-xl space-y-4">
        <header className="rounded-xl border border-slate-200 bg-white p-4">
          <h1 className="text-xl font-semibold text-slate-900">
            pywebview-start 模板
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            shadcn + React + pywebview 的最小前后端通信示例
          </p>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>基础任务</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="taskName">任务名称</Label>
              <Input
                id="taskName"
                value={taskName}
                onChange={(event) => setTaskName(event.target.value)}
                placeholder="输入一个任务名，例如：hello template"
                disabled={isRunning}
              />
            </div>

            <Button type="button" onClick={() => void runTask()} disabled={!canRun}>
              {isRunning ? (
                <>
                  <IconLoader2 data-icon="inline-start" className="animate-spin" />
                  调用中...
                </>
              ) : (
                <>
                  <IconBolt data-icon="inline-start" />
                  调用 Python 基础任务
                </>
              )}
            </Button>

            <p className="text-xs text-slate-500">
              连接状态: {isReady ? "已连接 pywebview" : "等待 pywebviewready"}
            </p>
            <p className="text-xs text-slate-500">
              Python state ticker: {typeof ticker === "number" ? ticker : "-"}
            </p>
          </CardContent>
        </Card>

        {result ? (
          <Alert className="border-emerald-200 bg-emerald-50 text-emerald-900">
            <IconCircleCheckFilled className="text-emerald-600" />
            <AlertTitle>调用成功</AlertTitle>
            <AlertDescription className="space-y-1 text-emerald-800">
              <p>{result.message}</p>
              <p>task: {result.task}</p>
              <p>time: {result.now}</p>
              <p>python: {result.python_version}</p>
              <p>platform: {result.platform}</p>
            </AlertDescription>
          </Alert>
        ) : null}

        {error ? (
          <Alert variant="destructive">
            <AlertTitle>调用失败</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}
      </main>
    </div>
  )
}

export default App
