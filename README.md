# pywebview-start

`pywebview-start` 是一个 `shadcn + React + pywebview` 桌面应用启动模板。

默认示例只保留了一个最基础的前后端通信任务：前端调用 Python `run_basic_task`，并把返回结果展示在页面上。

## 环境要求

- Python 3.13+
- Node.js + pnpm

## 安装依赖

```bash
pnpm install
uv sync
```

## 常用命令

- `pnpm dev`: 启动前端开发服务器（Vite）
- `pnpm frontend:dev`: 构建前端到 `gui/`（不压缩）
- `pnpm frontend:prod`: 构建前端到 `gui/`（压缩）
- `pnpm start`: 构建 `gui/` 后启动 pywebview 桌面应用
- `pnpm python:start:dev`: pywebview 直连开发服务器（默认 `http://localhost:5173`）

## 开发模式

1. 终端 A：`pnpm dev`
2. 终端 B：`pnpm python:start:dev`

如需修改开发服务器地址，可设置环境变量 `PYWEBVIEW_DEV_SERVER_URL`。

## 打包 Windows EXE

```bash
pnpm build:windows
```

可选清理后重打包：

```bash
pnpm build:windows:clean
```

打包输出目录为 `dist/pywebview-start/`，主程序为 `pywebview-start.exe`。
