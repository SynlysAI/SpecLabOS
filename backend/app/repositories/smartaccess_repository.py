"""SmartAccess 模板和运行记录仓储。"""

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.smartaccess import (
    SmartAccessRunCreateRequest,
    SmartAccessRunEventRequest,
    SmartAccessTemplatePublishRequest,
)


def _now_text() -> str:
    """返回当前 UTC ISO 时间文本。

    Returns:
        当前时间文本。
    """
    return datetime.now(timezone.utc).isoformat()


class SmartAccessRunNotFoundError(Exception):
    """SmartAccess 运行不存在错误。"""


class SmartAccessRepository:
    """SmartAccess 模板、运行和事件 MongoDB 仓储。"""

    def __init__(self, database) -> None:
        """初始化仓储。

        Args:
            database: MongoDB 数据库实例。
        """
        self._templates = database["smartaccess_templates"]
        self._runs = database["smartaccess_runs"]
        self._events = database["smartaccess_run_events"]

    def publish_template(
        self,
        payload: SmartAccessTemplatePublishRequest,
    ) -> dict:
        """保存或更新 SmartAccess 模板快照。

        Args:
            payload: 模板发布请求。

        Returns:
            模板记录。
        """
        now = _now_text()
        workflow = payload.workflow
        metadata = workflow.get("metadata", {}) if isinstance(workflow, dict) else {}
        steps = workflow.get("steps", []) if isinstance(workflow, dict) else []
        record = {
            "template_id": payload.template_id,
            "template_version": payload.template_version,
            "workflow_id": payload.workflow_id or metadata.get("workflow_id", ""),
            "name": payload.name or payload.workflow_id or payload.template_id,
            "description": payload.description,
            "anchor_profile": payload.anchor_profile
            or metadata.get("anchor_profile", ""),
            "source_device_id": payload.source_device_id,
            "source": "smartaccess",
            "status": "published",
            "step_count": len(steps) if isinstance(steps, list) else 0,
            "workflow": workflow,
            "published_by": payload.published_by,
            "updated_at": now,
        }
        existing = self._templates.find_one(
            {
                "template_id": payload.template_id,
                "template_version": payload.template_version,
            }
        )
        if existing:
            record["published_at"] = existing.get("published_at", now)
        else:
            record["published_at"] = now
        self._templates.update_one(
            {
                "template_id": payload.template_id,
                "template_version": payload.template_version,
            },
            {"$set": record},
            upsert=True,
        )
        return dict(record)

    def list_templates(
        self,
        keyword: str | None = None,
        device_id: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """查询 SmartAccess 模板列表。

        Args:
            keyword: 搜索关键字。
            device_id: 目标设备或锚点配置。
            status: 模板状态。

        Returns:
            模板记录列表。
        """
        query: dict = {}
        if status:
            query["status"] = status
        if device_id:
            query["anchor_profile"] = device_id
        records = list(self._templates.find(query).sort("updated_at", -1))
        if keyword:
            needle = keyword.lower()
            records = [
                item for item in records
                if needle in " ".join(
                    [
                        str(item.get("template_id", "")),
                        str(item.get("template_version", "")),
                        str(item.get("workflow_id", "")),
                        str(item.get("name", "")),
                        str(item.get("anchor_profile", "")),
                    ]
                ).lower()
            ]
        return records

    def get_template(self, template_id: str, template_version: str) -> dict | None:
        """读取指定模板版本。

        Args:
            template_id: 模板 ID。
            template_version: 模板版本。

        Returns:
            模板记录，不存在时返回 None。
        """
        return self._templates.find_one(
            {"template_id": template_id, "template_version": template_version}
        )

    def delete_template(self, template_id: str, template_version: str) -> bool:
        """删除指定模板版本。

        Args:
            template_id: 模板 ID。
            template_version: 模板版本。

        Returns:
            是否成功删除。
        """
        result = self._templates.delete_one(
            {"template_id": template_id, "template_version": template_version}
        )
        return result.deleted_count > 0

    def create_run(
        self,
        template: dict,
        payload: SmartAccessRunCreateRequest,
    ) -> dict:
        """创建 SmartAccess 远程运行记录。

        Args:
            template: 模板记录。
            payload: 运行创建请求。

        Returns:
            运行记录。
        """
        workflow = dict(template.get("workflow") or {})
        record = {
            "run_id": f"sa_run_{uuid4().hex[:12]}",
            "template_id": payload.template_id,
            "template_version": payload.template_version,
            "workflow_id": template.get("workflow_id", ""),
            "workflow_name": template.get("name", ""),
            "smartaccess_node_id": payload.smartaccess_node_id,
            "target_device_id": payload.target_device_id,
            "anchor_profile": template.get("anchor_profile", ""),
            "status": "queued",
            "current_step_index": 0,
            "total_steps": int(template.get("step_count") or 0),
            "requested_by": payload.requested_by,
            "requested_at": _now_text(),
            "started_at": None,
            "finished_at": None,
            "workflow_snapshot": workflow,
            "summary": {},
            "last_error": "",
        }
        self._runs.insert_one(record)
        return dict(record)

    def list_runs(self) -> list[dict]:
        """查询 SmartAccess 运行列表。

        Returns:
            运行记录列表。
        """
        return list(self._runs.find({}).sort("requested_at", -1))

    def get_run(self, run_id: str) -> dict | None:
        """读取 SmartAccess 运行详情。

        Args:
            run_id: 平台运行 ID。

        Returns:
            运行记录，不存在时返回 None。
        """
        record = self._runs.find_one({"run_id": run_id})
        if record is None:
            return None
        record["events"] = list(
            self._events.find({"run_id": run_id}).sort("created_at", 1)
        )
        return record

    def append_event(
        self,
        run_id: str,
        payload: SmartAccessRunEventRequest,
    ) -> dict:
        """追加运行事件并推进运行状态。

        Args:
            run_id: 平台运行 ID。
            payload: 事件请求。

        Returns:
            事件记录。
        """
        if self._runs.find_one({"run_id": run_id}) is None:
            raise SmartAccessRunNotFoundError("SmartAccess 运行不存在")

        existing = self._events.find_one(
            {"run_id": run_id, "event_id": payload.event_id}
        )
        if existing:
            return existing
        event = {
            "event_id": payload.event_id,
            "run_id": run_id,
            "event_type": payload.event_type,
            "step_id": payload.step_id,
            "step_index": payload.step_index,
            "status": payload.status,
            "payload": payload.payload,
            "created_at": _now_text(),
        }
        self._events.insert_one(event)
        self._apply_event_to_run(run_id, event)
        return dict(event)

    def _apply_event_to_run(self, run_id: str, event: dict) -> None:
        """根据事件更新运行记录。

        Args:
            run_id: 平台运行 ID。
            event: 已落库事件。
        """
        status = event.get("status") or ""
        event_type = event.get("event_type") or ""
        updates: dict = {}
        if status:
            updates["status"] = status
        if event_type == "step.completed" and event.get("step_index") is not None:
            # 步骤完成时把进度推进到"已完成步骤数 = step_index + 1"
            updates["current_step_index"] = int(event["step_index"]) + 1
        elif event_type == "run.completed":
            # 运行完成时兜底把进度推到总数，避免最后一步完成后 run 级事件丢失导致少 1
            run = self._runs.find_one({"run_id": run_id})
            if run:
                updates["current_step_index"] = int(run.get("total_steps") or 0)
        if event_type == "run.started":
            updates["started_at"] = event["created_at"]
            updates["status"] = status or "running"
        if event_type in {"run.completed", "run.failed", "run.cancelled", "run.rejected"}:
            updates["finished_at"] = event["created_at"]
        if status in {"failed", "rejected"}:
            updates["last_error"] = str(event.get("payload", {}).get("error", ""))
        if updates:
            self._runs.update_one({"run_id": run_id}, {"$set": updates})
