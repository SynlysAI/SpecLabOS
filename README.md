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
