# Spectrum Alab 设备同步与工作流编排改造设计

## 1. 目标

将 `E:\github_project\SpecLabOS\examples\spectrum_alab` 中的设备目录、连接配置和动作定义同步到当前 `SpecLabOS` 项目中，并完成以下改造：

- 当前项目同步原项目全部设备实例。
- 已有真实接口定义的设备迁移真实动作和参数描述。
- 仅依赖原项目基类默认启停/状态能力的设备保留模拟动作，不伪装成真实接入。
- 工作流编排改为“单设备顺序动作编排”。
- 工作流步骤参数由动作 `parameter_schema` 动态驱动渲染。
- 本次改造不要求对真实设备联通性做自动验证，避免因当前网络不可达阻塞功能接入。

## 2. 原项目配置基线

原项目 `config.toml` 中可迁移的基础配置如下：

### 2.1 基础设施

- MongoDB: `100.84.59.58:27018`
- MongoDB 用户名: `admin`
- MongoDB 密码: `password123`
- RabbitMQ: `100.84.59.58:5672`
- RabbitMQ 用户名: `admin`
- RabbitMQ 密码: `password123`

### 2.2 设备接口地址

- GPC API: `http://100.74.253.59:8001`
- Resin API: `http://47.113.220.254:7000`
- Resin 多实例映射:
  - `resin_2278`
  - `resin_2278_2`
  - `resin_1438`
- Station API: `http://47.113.220.254:7001`
- PI API: `http://47.113.220.254:6667`
- NMR API: `http://127.0.0.1:18080`
- Raman 采集 API: `http://47.113.220.254:7001`
- Raman 结果 API: `http://47.113.220.254:7002`

### 2.3 图片目录

- 图片目录继续复用：`E:\github_project\SpecLabOS\examples\spectrum_alab\alabos_project\images`

## 3. 设备同步范围

### 3.1 全量同步设备实例

本次同步以下全部设备：

- `nmr_2278`
- `gpc_2278`
- `pi_2278`
- `ir_2278`
- `raman_2278`
- `lcms_2278`
- `resin_2278`
- `resin_2278_2`
- `resin_1438`
- `metal_108`
- `cat_108`
- `micro_108`

### 3.2 真实接口设备

以下设备在原项目中具备明确的远程接口定义，本次迁移其真实动作模型与参数结构：

- `NMR`
- `GPC`
- `PI`
- `Resin`
- `Raman`
- `Station` 系列

### 3.3 模拟设备

以下设备在原项目中没有独立真实接口实现，仅依赖基类默认启停和状态逻辑：

- `IR`
- `LCMS`

这两类设备在当前项目中仅保留模拟动作，不额外增加真实接口层。

## 4. 后端设计

## 4.1 配置模型扩展

当前 `config.yaml` 只包含简单 Mongo 配置和运行参数，需扩展为可描述 spectrum_alab 原项目连接信息的结构。建议新增：

- `mongo.uri`
- `mongo.database`
- `mongo.completed_uri`
- `mongo.completed_database`
- `rabbitmq.host`
- `rabbitmq.port`
- `rabbitmq.username`
- `rabbitmq.password`
- `device_images.image_dir`
- `apis.gpc.base_url`
- `apis.resin.base_url`
- `apis.resin.devices`
- `apis.station.base_url`
- `apis.pi.base_url`
- `apis.nmr.base_url`
- `apis.nmr.timeout`
- `apis.raman.capture_base_url`
- `apis.raman.result_base_url`
- `apis.raman.timeout`

当前项目如暂时未消费某些配置，也先完整落入配置模型，避免后续再次破坏结构。

## 4.2 设备抽象策略

当前 `BaseDevice` 已支持：

- 设备元数据
- 连接信息 `connection`
- 动作目录 `actions`
- 动作执行器 `executor`

本次不推翻现有抽象，而是在现有抽象上扩展：

- 为真实设备增加独立设备模块，封装真实 HTTP 调用逻辑。
- 为模拟设备保留轻量 executor。
- 设备工厂从“硬编码动作”改为“构建真实设备对象或模拟设备对象”。
- 设备序列化结果中暴露连接摘要，便于前端查看设备接入来源。

## 4.3 动作目录迁移

### NMR

- `nmr.upload_task_info`
- `nmr.start_task`
- `nmr.get_task_status`
- `nmr.list_templates`
- `nmr.change_params`
- `nmr.agv_interact`

### GPC

- `gpc.initialize`
- `gpc.pause`
- `gpc.reset`
- `gpc.start_project`
- `gpc.get_device_status_detail`
- `gpc.get_current_tasks`
- `gpc.upload_task_data`

### PI

- `pi.health_check`
- `pi.power_on`
- `pi.pause`
- `pi.power_off`

`pi.get_config` 和 `pi.update_config` 在原项目中为 `NotImplemented`，本次不接入为真实动作，避免暴露不可用动作。

### Resin

- `resin.health_check`
- `resin.trigger_generate`
- `resin.execute_process`
- `resin.get_experiment_status`

### Raman

- `raman.capture`
- `raman.get_result`

### Station

按 `metal_108`、`cat_108`、`micro_108` 三个实例接入：

- `<device>.power_on`
- `<device>.power_off`
- `<device>.check_status`

### 模拟设备

`IR` 与 `LCMS` 保留模拟动作：

- `check_status`
- `power_on`
- `power_off`

## 4.4 参数 Schema 规范

所有设备动作均返回统一的 `parameter_schema` 描述，字段至少包括：

- `name`
- `type`
- `required`
- `description`

类型范围至少支持：

- `string`
- `number`
- `boolean`
- `json`

其中：

- Raman 的 `capture` 参数使用 `json`
- GPC 的批量任务数据使用 `json`
- NMR 的复杂参数列表使用 `json`
- Station 的启停和状态查询通常无参数

## 4.5 工作流数据约束

工作流创建时必须满足：

- 所有步骤属于同一个 `device_key`
- 步骤按添加顺序执行
- 每一步的 `params` 原样落库
- 不在创建时校验远程接口是否可达

后端在 `create_workflow` 时增加单设备校验。若步骤内出现多个设备，直接返回 400。

## 5. 前端设计

## 5.1 编排模式调整

当前编排界面是“每步选择设备、每步选择动作”。本次改为：

1. 先选工作流目标设备
2. 加载该设备动作目录
3. 连续为该设备添加多个动作步骤
4. 提交整个单设备顺序工作流

页面顶层字段调整为：

- 工作流名称
- 创建人
- 目标设备

步骤配置字段调整为：

- 步骤名称
- 动作选择
- 动作参数表单
- 执行说明

## 5.2 动态参数表单

前端根据动作的 `parameter_schema` 动态渲染参数输入组件：

- `string` -> `Input`
- `number` -> `InputNumber`
- `boolean` -> `Switch` 或 `Select`
- `json` -> `Input.TextArea`

提交时：

- `json` 字段先进行 `JSON.parse`
- 校验失败则阻止添加步骤
- 成功后写入 `params`

## 5.3 步骤展示

步骤列表展示以下信息：

- 序号
- 步骤名称
- 动作名称
- 参数摘要
- 执行说明

首版至少支持：

- 添加步骤
- 删除步骤

如当前项目已有可复用排序能力，可再增加排序；若无，则本次不强行加入拖拽。

## 5.4 设备动作可见性

对于未实现真实接口但保留模拟动作的设备，前端照常展示动作并允许编排。

对于原项目中声明了但并未真实实现的动作，不在前端动作目录中暴露，避免误导用户。例如：

- `pi.get_config`
- `pi.update_config`

## 6. 数据库与接口行为

## 6.1 Mongo 数据落点

工作流定义仍存 `workflow_definitions`。

工作流运行记录仍存 `workflow_runs`。

本次改造不改变两张集合的总体职责，仅补充更完整的步骤参数内容。

## 6.2 设备接口

保留当前接口形式：

- `GET /api/devices`
- `GET /api/devices/{device_key}`
- `GET /api/devices/{device_key}/actions`

其中动作接口返回应包含：

- `action_key`
- `name`
- `description`
- `step_mode`
- `parameter_schema`

## 7. 错误处理

- 设备动作接口配置缺失时，设备仍可注册，但执行动作时返回明确错误。
- 远程接口超时或连接失败时，动作执行器返回错误结果，不在设备目录构建时提前失败。
- 前端对 JSON 参数格式错误立即阻断，不提交后端。
- 后端对多设备工作流直接拒绝。

## 8. 测试策略

本次以结构测试和接口测试为主，不做真实设备联通测试。

后端至少补充：

- 全量设备目录返回测试
- 设备动作目录 schema 测试
- 单设备工作流创建成功测试
- 多设备工作流创建失败测试
- 动作参数原样保存测试

前端至少覆盖：

- 设备选择后加载动作目录
- 动态参数表单渲染
- JSON 参数解析失败提示
- 提交单设备工作流请求结构正确

## 9. 实施顺序

1. 扩展配置模型与配置文件
2. 重构设备工厂并同步全量设备清单
3. 为真实设备接入 HTTP 动作执行器
4. 保留 IR、LCMS 模拟设备
5. 扩展设备动作接口返回完整参数 schema
6. 改造前端工作流编排页为单设备模式
7. 增加动态参数表单
8. 增加后端单设备校验与测试
9. 补充前端交互验证

## 10. 非目标

本次不包含以下内容：

- 实际设备联通性验证
- RabbitMQ 任务编排接入
- 已完成实验数据库读写接入
- 复杂工作流条件分支
- 多设备混排工作流
