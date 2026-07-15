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
- RabbitMQ routing key：`device.{smartaccess_node_id}.run.requested`
- 设备队列建议：`smartaccess.device.{smartaccess_node_id}.commands`

`config.yaml` 中配置 `smartaccess.api_token` 后，SmartAccess HTTP 接口会要求请求携带 `Authorization: Bearer <token>`。平台发起运行时，后端创建 `smartaccess_runs` 记录，并通过 RabbitMQ 把任务投递给指定 `smartaccess_node_id` 的 SmartAccess worker。

`smartaccess_node_id` 表示安装并运行 SmartAccess worker 的执行端电脑 ID；`target_device_id` 表示该电脑控制的目标设备或目标软件，例如 `vpn软件`、`weixin`。任务运行列表中的“目标设备”展示 `target_device_id`，“执行端”展示 `smartaccess_node_id`。

## SmartDataHub 数据入库

SpecLabOS 当前也集成了 SmartDataHub 的数据接收能力，用于接收设备端 Collector 上报的文件，并写入 MinIO 和 MongoDB。

### 接口

- 文件上传：`POST /api/data/ingest/files`
- 资产列表：`GET /api/data/assets`
- 资产文件列表：`GET /api/data/assets/{asset_id}/files`

### 存储结构

MongoDB 使用两个集合：

- `data_assets`：资产主记录，表示一个结果目录或一个单文件资产。
- `data_asset_files`：文件明细记录，表示资产下的每个具体文件。

### ID 规则

当前资产和文件主键使用确定性 UUID 生成，避免同名目录冲突。

- `asset_key = device_id:data_type:asset_group_id`
- `asset_id = uuid5(namespace, asset_key)`
- `file_key = asset_key:relative_path`
- `file_id = uuid5(namespace, file_key)`

其中：

- `asset_group_id` 是业务上的结果目录名或文件名，例如 `sample_005`。
- `relative_path` 是文件在结果目录内的相对路径，例如 `pdata/1/1r`。

### 数据含义

- `data_assets`：保存资产汇总信息，例如 `file_count`、`total_size`、`storage_prefix`、`upload_status`。
- `data_asset_files`：保存每个文件的详细信息，例如 `relative_path`、`file_hash`、`storage_key`、`storage_uri`。

对于目录型结果，`data_assets` 代表整个结果目录，`data_asset_files` 代表目录中的每个文件。

### MinIO 规则

目录型资产会按原目录结构上传到 MinIO，不做 zip 压缩。对象 key 形如：

```text
data-assets/{device_id}/{data_type}/{yyyy}/{mm}/{dd}/{root_name}/{relative_path}
```

如果是单文件资产，则不会附加根目录名。

### Collector 协作方式

Collector 监听设备端目录并上报文件内容，SpecLabOS 负责：

- 接收上传文件
- 写入 MinIO
- 更新 MongoDB 主记录和文件明细
- 提供资产列表和文件列表查询接口

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
