# SpecLabOS

SpecLabOS 用于统一管理实验设备、工作流编排与任务运行。

## 本地运行

1. 创建并激活环境

```powershell
conda create -n SpecLabOS python=3.12 -y
conda activate SpecLabOS
```

如果你当前沿用旧项目环境，也可以继续使用已有的 `alabos` 环境；两者任选其一，但需确保 `backend/requirements.txt` 与前端依赖都已安装。

2. 安装后端依赖

```powershell
cd E:\xx_project\SpecLabOS\backend
pip install -r requirements.txt
```

3. 启动后端服务

```powershell
cd E:\xx_project\SpecLabOS\backend
uvicorn main:app --reload
# 或者
uvicorn main:app --host 0.0.0.0 --port 8010
```

4. 安装并启动前端

```powershell
cd E:\xx_project\SpecLabOS\frontend
npm install
npm run dev
```

## 当前接口状态

- 已可用的后端占位接口：
  - `GET /api/devices`
  - `GET /api/workflows`
  - `GET /api/workflow-runs`
  - `GET /api/workflow-runs/{run_id}`
  - `GET /api/logs`
- 当前前端页面会优先请求这些接口。
- 当接口不可用或字段尚未完全对齐时，页面会回退到前端内置示例数据，并显示提示信息。

## SmartAccess 模板中心

SpecLabOS 提供独立的 SmartAccess 模板中心，用于接收 SmartAccess 桌面端发布的 workflow 模板，并发起远程运行任务。

- 模板发布接口：`POST /api/smartaccess/templates/publish`
- 模板查看入口：前端“SmartAccess 模板”页
- 运行状态回传：`POST /api/smartaccess/runs/{run_id}/events`
- RabbitMQ exchange：`smartaccess.commands`
- RabbitMQ routing key：`device.{device_id}.run.requested`
- 设备队列建议：`smartaccess.device.{device_id}.commands`

`config.yaml` 中配置 `smartaccess.api_token` 后，SmartAccess HTTP 接口会要求请求携带 `Authorization: Bearer <token>`。平台发起运行时，后端创建 `smartaccess_runs` 记录，并通过 RabbitMQ 把任务投递给指定 `device_id` 的 SmartAccess worker。

## 基础验证

后端测试：

```powershell
cd E:\xx_project\SpecLabOS\backend
pytest -v
```

前端构建：

```powershell
cd E:\xx_project\SpecLabOS\frontend
npm run build
```
