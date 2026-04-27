# SpecLabOS 设计文档

## 1. 项目目标

SpecLabOS 是一个面向实验室自动化场景的轻量级设备任务平台，部署在单机环境中，主要服务于 `examples\spectrum_alab` 下已有实验设备的监控与自动化任务执行。

第一版仅聚焦以下能力：

1. 设备状态监控
2. 表单式顺序工作流编排与下发
3. 任务运行进度查询
4. 任务执行历史与日志记录

本项目不沿用 `alab_management` 的实验、样品、任务依赖图等复杂模型，也不依赖环境变量形式的项目配置。

---

## 2. 设计原则

### 2.1 简单优先

第一版只实现顺序工作流，不实现并行分支、条件分支、复杂资源调度、样品管理、权限系统等超出当前需求的功能。

### 2.2 设备中心化

系统围绕“设备”和“设备动作”建模，而不是围绕“实验”和“样品”建模。

### 2.3 平台注册设备，设备内部声明动作

平台层只负责加载和注册设备。每个设备模块内部自行声明支持的动作、参数 schema、确认 schema 以及实际执行逻辑。

### 2.4 本地固定配置

系统默认从项目根目录读取本地配置文件，不依赖 `ALABOS_CONFIG_PATH` 或 `SIM_MODE_FLAG` 之类的环境变量。

### 2.5 单机单体可维护

第一版采用单机单体架构，但代码内部按 API、服务、领域、设备适配、基础设施分层，确保后续可扩展。

---

## 3. 总体架构

系统由以下五层组成：

### 3.1 API 层

负责向前端提供 HTTP 接口，包括：

- 设备列表与设备详情
- 设备动作元数据
- 工作流创建与查询
- 工作流运行详情与日志
- 设备启用/禁用

### 3.2 应用服务层

负责业务流程编排，包括：

- 设备注册同步
- 工作流定义创建
- 工作流运行创建
- 步骤执行调度
- 状态轮询与状态更新
- 运行取消

### 3.3 领域层

定义系统核心对象：

- `Device`
- `ActionSpec`
- `WorkflowDefinition`
- `WorkflowRun`
- `StepRun`

领域层中不出现 `Experiment`、`Sample` 等旧模型。

### 3.4 设备适配层

每台设备对应一个独立模块，封装：

- 设备身份信息
- 连接配置
- 状态读取逻辑
- 动作定义
- 动作执行逻辑

### 3.5 基础设施层

负责：

- MongoDB 访问
- 配置加载
- 后台轮询器
- 运行器线程
- 系统日志写入

---

## 4. 项目目录设计

项目根目录位于：

`E:\xx_project\SpecLabOS`

建议目录结构如下：

```text
E:\xx_project\SpecLabOS
├─ backend
│  ├─ app
│  │  ├─ api
│  │  ├─ core
│  │  ├─ domain
│  │  ├─ services
│  │  ├─ devices
│  │  ├─ repositories
│  │  ├─ runners
│  │  └─ schemas
│  ├─ scripts
│  ├─ tests
│  └─ main.py
├─ frontend
│  ├─ src
│  │  ├─ layout
│  │  ├─ pages
│  │  ├─ components
│  │  ├─ modules
│  │  ├─ services
│  │  └─ styles
├─ docs
├─ config.yaml
└─ README.md
```

---

## 5. 技术选型

### 5.1 后端

- Python 3.11
- FastAPI
- Pydantic
- PyMongo
- Uvicorn
- 轻量后台线程或 APScheduler

选择理由：

- FastAPI 便于动作参数 schema 管理和接口文档生成
- Pydantic 便于表单参数定义和校验
- PyMongo 可直接复用现有 MongoDB 服务
- 无需引入 RabbitMQ、Dramatiq 等复杂执行基础设施

### 5.2 前端

- React
- Vite
- Ant Design
- React Router

选择理由：

- React 便于快速落地
- Ant Design 更适合企业后台风格界面
- 能满足表格、抽屉、表单、状态标记等管理台需求

### 5.3 环境

建议新建 conda 环境：

`SpecLabOS`

此环境专用于新项目，与旧项目环境解耦。

---

## 6. 配置设计

系统默认读取项目根目录下的 `config.yaml`，配置内容包括但不限于：

- MongoDB 连接信息
- 目标数据库名：`spec_labos`
- 全局模拟模式配置
- 启用设备列表
- 设备连接配置
- 状态轮询间隔
- 运行器检查间隔

配置文件为第一优先级，不通过环境变量覆盖。

---

## 7. 数据库设计

复用现有 MongoDB 服务，创建独立数据库：

`spec_labos`

第一版定义六个核心集合。

### 7.1 `devices`

保存设备主数据和当前配置。

建议字段：

- `key`
- `name`
- `category`
- `enabled`
- `sim_mode`
- `connection`
- `status_snapshot`
- `capabilities`
- `updated_at`

### 7.2 `device_action_specs`

保存动作定义元数据。

建议字段：

- `action_key`
- `device_key`
- `device_category`
- `name`
- `description`
- `step_mode`
- `parameter_schema`
- `confirm_schema`
- `timeout_config`
- `enabled`

### 7.3 `workflow_definitions`

保存工作流定义。

建议字段：

- `workflow_id`
- `name`
- `description`
- `source`
- `steps`
- `tags`
- `created_by`
- `created_at`

其中 `steps` 为顺序数组，每项包含：

- `step_id`
- `device_key`
- `action_key`
- `params`
- `confirm_params`
- `display_name`

### 7.4 `workflow_runs`

保存工作流运行实例。

建议字段：

- `run_id`
- `workflow_id`
- `workflow_name`
- `status`
- `current_step_index`
- `total_steps`
- `started_at`
- `finished_at`
- `created_by`
- `trigger_source`
- `summary`

### 7.5 `step_runs`

保存步骤运行记录。

建议字段：

- `run_id`
- `step_id`
- `step_index`
- `device_key`
- `action_key`
- `status`
- `params`
- `confirm_params`
- `started_at`
- `finished_at`
- `result`
- `error_message`
- `logs_ref`

### 7.6 `system_logs`

保存平台日志与设备执行日志。

建议字段：

- `scope`
- `ref_id`
- `level`
- `message`
- `payload`
- `created_at`

---

## 8. 设备注册与动作声明模型

### 8.1 设备注册原则

平台层只注册设备，不在平台入口平铺注册所有任务类。

系统启动时扫描 `backend/app/devices/` 下的设备模块，将启用设备注册到内存中的 `DeviceRegistry`，并同步到 MongoDB。

### 8.2 设备模块职责

每个设备模块至少提供：

- 基本信息：`key/name/category/enabled/sim_mode`
- 连接配置
- `get_status()`
- `list_actions()`
- `execute_action(action_key, params, context)`

### 8.3 动作定义模型

每个设备内部维护自己的动作定义列表。动作定义包括：

- `action_key`
- `name`
- `description`
- `parameter_schema`
- `confirm_schema`
- `step_mode`
- `executor`

动作示例：

- `nmr.check_status`
- `nmr.upload_task_info`
- `nmr.start_task`
- `gpc.initialize`
- `gpc.upload_batch_task_data`
- `resin.trigger_generate`

### 8.4 两步动作处理原则

第一版将两步动作视为编排阶段特性，而非运行时复杂状态机。

动作类型分为：

- `single_step`
- `two_phase`

对于 `two_phase` 动作：

1. 用户先填写主参数
2. 后端执行预检查或生成确认信息
3. 前端展示确认表单
4. 用户确认后，该步骤作为完整步骤加入工作流

运行期不再拆成额外子步骤系统。

---

## 9. 工作流模型与执行规则

### 9.1 工作流模型

第一版工作流为严格顺序步骤列表，不支持并行分支、条件跳转和复杂 DAG。

每个工作流由多个步骤组成，每一步绑定一个设备和一个动作。

### 9.2 执行器行为

工作流运行器执行过程如下：

1. 创建 `workflow_run`
2. 按顺序读取步骤
3. 为当前步骤写入 `step_run`
4. 检查目标设备是否可执行
5. 调用设备动作执行器
6. 更新步骤状态
7. 成功则进入下一步
8. 失败则终止运行并标记工作流失败
9. 用户取消则标记取消并停止后续步骤

### 9.3 并发与互斥规则

第一版采用轻量设备互斥机制：

- 不同设备任务允许并发执行
- 同一设备任务默认串行执行
- 只读状态查询不占用设备锁
- 正在轮询等待完成的执行步骤持续占用该设备

即：

- 如果工作流 A 正在等待设备 `nmr_2278` 完成任务，则该设备视为占用中
- 同时提交面向 `gpc_2278` 的工作流，可以立即执行
- 同时提交面向 `nmr_2278` 的另一个工作流，可以提交，但进入等待设备状态

这不是复杂资源调度系统，而是第一版必须具备的最小设备互斥能力。

### 9.4 状态定义建议

工作流运行状态建议包含：

- `pending`
- `queued`
- `running`
- `success`
- `failed`
- `cancelled`

步骤状态建议包含：

- `pending`
- `waiting_device`
- `running`
- `success`
- `failed`
- `cancelled`

---

## 10. 设备监控设计

设备监控与工作流执行解耦。

平台启动后运行后台状态轮询器，定时读取所有启用设备的当前状态：

1. 调用设备 `get_status()`
2. 更新 `devices.status_snapshot`
3. 对关键状态变化写入 `system_logs`

设备监控页始终基于 `devices` 集合读取，不依赖工作流运行态。

---

## 11. 前端信息架构

第一版采用企业后台式实验平台界面，不采用 demo 风格卡片堆砌布局。

### 11.1 一级导航

建议包含四个主模块：

1. 设备监控
2. 工作流编排
3. 任务运行
4. 系统日志

### 11.2 核心页面

#### 设备监控列表页

字段建议：

- 设备名称
- 分类
- 当前状态
- 启用状态
- 模拟模式
- 最后更新时间
- 最近消息
- 操作

#### 设备详情页或抽屉

展示：

- 基本信息
- 连接配置摘要
- 支持动作列表
- 最近状态快照
- 最近日志

#### 工作流编排页

采用表单式顺序编排，而非节点画布。

编排流程：

1. 选择设备
2. 选择动作
3. 动态加载参数表单
4. 若为两步动作，则完成确认表单
5. 添加至步骤列表
6. 支持上移、下移、复制、删除
7. 保存并提交执行

#### 任务运行列表页

字段建议：

- 运行编号
- 工作流名称
- 当前状态
- 当前步骤
- 提交时间
- 开始时间
- 结束时间
- 创建人
- 操作

#### 任务运行详情页

展示：

- 工作流基本信息
- 步骤执行时间线
- 每一步状态
- 输入参数
- 执行结果
- 错误信息
- 相关日志

#### 系统日志页

支持按以下条件过滤：

- 日志级别
- 日志范围
- 时间范围
- 关键字

### 11.3 视觉风格

界面风格应偏向企业后台、实验平台、设备管理系统：

- 左侧固定导航
- 顶部操作区
- 中间主内容区
- 以表格、抽屉、表单、状态标签为主
- 浅色背景
- 蓝色为主色
- 状态颜色清晰分层

不采用玩具化展示风格，不采用大面积无信息量可视化。

---

## 12. 运行方式

第一版运行方式如下：

1. 启动后端服务
2. 读取 `config.yaml`
3. 注册启用设备
4. 同步设备与动作定义到 Mongo
5. 启动后台状态轮询器
6. 启动后台工作流运行器
7. 前端通过 HTTP API 与后端交互

第一版不拆分微服务，不引入消息队列，不做分布式部署。

---

## 13. 第一版功能范围

### 13.1 必做功能

1. 设备状态监控
2. 表单式顺序工作流编排
3. 任务运行进度查询
4. 任务执行历史与日志记录

### 13.2 预留但不实现

1. 工作流文件导入
2. 工作流模板中心
3. 节点画布编排
4. 用户与权限系统

---

## 14. 第一版非目标

以下内容明确不纳入第一版：

- 样品管理
- 实验对象模型
- 项目/课题管理
- 用户登录
- 角色权限
- 并行步骤
- 条件分支
- 复杂任务依赖图
- 复杂设备资源仲裁
- 消息队列与分布式执行
- 设备远程 agent 系统
- 热插拔动态驱动市场

---

## 15. 结论

SpecLabOS 第一版应当被定义为一个“专业、轻量、可扩展的实验设备自动化平台骨架”，而不是完整的实验室操作系统。

第一版成功标准为：

1. 已有 `spectrum_alab` 相关设备可接入新平台
2. 每台设备可声明自己的动作和参数 schema
3. 前端可通过表单完成顺序工作流编排
4. 后端可执行工作流并记录运行结果
5. 跨设备任务可并发，同设备任务串行
6. 用户可查询设备状态、任务进度和历史日志

满足以上标准后，再考虑工作流导入、模板化、可视化编排等二阶段能力。
