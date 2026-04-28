"""GPC 设备定义。"""

from typing import Any

from app.devices.base import BaseDevice
from app.domain.device_action import ActionSpec


def _run_simple_action(action_name: str):
    """构造 GPC 的简单模拟动作。"""

    def _executor(params: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
        return {
            "device": "gpc_2278",
            "action": action_name,
            "status": "completed",
            "response": params,
        }

    return _executor


def build_gpc_device(sim_mode: bool) -> BaseDevice:
    """构建 GPC 设备实例。

    Args:
        sim_mode: 是否启用模拟模式。

    Returns:
        预留后续扩展的 GPC 设备实例。
    """
    return BaseDevice(
        key="gpc_2278",
        name="gpc_2278",
        category="凝胶渗透色谱仪",
        device_type="GPCAnalyzer",
        location="A-105",
        sim_mode=sim_mode,
        actions=[
            ActionSpec(
                action_key="gpc.initialize",
                name="初始化",
                description="初始化 GPC 设备",
                executor=_run_simple_action("initialize"),
            ),
            ActionSpec(
                action_key="gpc.upload_batch_task_data",
                name="上传任务数据",
                description="上传 GPC 批次任务数据",
                parameter_schema=[
                    {"name": "task_data", "type": "json", "required": True},
                ],
                executor=_run_simple_action("upload_batch_task_data"),
            ),
            ActionSpec(
                action_key="gpc.start_project",
                name="项目开始",
                description="启动 GPC 当前项目",
                executor=_run_simple_action("start_project"),
            ),
            ActionSpec(
                action_key="gpc.check_device_detail_status",
                name="查询设备明细状态",
                description="查询 GPC 设备耗材与模块状态",
                executor=_run_simple_action("check_device_detail_status"),
            ),
            ActionSpec(
                action_key="gpc.get_current_tasks",
                name="获取当前批次记录数据",
                description="获取 GPC 当前批次记录数据",
                executor=_run_simple_action("get_current_tasks"),
            ),
        ],
    )
