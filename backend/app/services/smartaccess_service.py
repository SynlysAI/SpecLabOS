"""SmartAccess 平台集成服务。"""

from fastapi import HTTPException

from app.repositories.smartaccess_repository import SmartAccessRepository
from app.schemas.smartaccess import (
    SmartAccessRunCreateRequest,
    SmartAccessRunEventRequest,
    SmartAccessTemplatePublishRequest,
)


class SmartAccessService:
    """SmartAccess 模板和远程运行业务服务。"""

    def __init__(self, repository: SmartAccessRepository, publisher) -> None:
        """初始化服务。

        Args:
            repository: SmartAccess 仓储。
            publisher: SmartAccess MQ 发布器。
        """
        self._repository = repository
        self._publisher = publisher

    def publish_template(self, payload: SmartAccessTemplatePublishRequest) -> dict:
        """发布 SmartAccess 模板。

        Args:
            payload: 模板发布请求。

        Returns:
            模板记录。
        """
        if not payload.workflow:
            raise HTTPException(status_code=400, detail="workflow 不能为空")
        return self._repository.publish_template(payload)

    def list_templates(
        self,
        keyword: str | None = None,
        device_id: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """查询模板列表。

        Args:
            keyword: 搜索关键字。
            device_id: 设备 ID。
            status: 模板状态。

        Returns:
            模板列表。
        """
        return self._repository.list_templates(keyword, device_id, status)

    def get_template(self, template_id: str, template_version: str) -> dict:
        """读取模板详情。

        Args:
            template_id: 模板 ID。
            template_version: 模板版本。

        Returns:
            模板记录。
        """
        template = self._repository.get_template(template_id, template_version)
        if template is None:
            raise HTTPException(status_code=404, detail="SmartAccess 模板不存在")
        return template

    def create_run(self, payload: SmartAccessRunCreateRequest) -> dict:
        """创建 SmartAccess 远程运行并发布 MQ 消息。

        Args:
            payload: 运行创建请求。

        Returns:
            运行记录。
        """
        template = self.get_template(payload.template_id, payload.template_version)
        run = self._repository.create_run(template, payload)
        self._publisher.publish_run_requested(
            {
                "message_id": f"msg_{run['run_id']}",
                "type": "run.requested",
                "run_id": run["run_id"],
                "template_id": run["template_id"],
                "template_version": run["template_version"],
                "device_id": run["device_id"],
                "workflow": run["workflow_snapshot"],
                "requested_by": run["requested_by"],
                "requested_at": run["requested_at"],
            }
        )
        return run

    def append_event(
        self,
        run_id: str,
        payload: SmartAccessRunEventRequest,
    ) -> dict:
        """追加 SmartAccess 运行事件。

        Args:
            run_id: 平台运行 ID。
            payload: 事件请求。

        Returns:
            事件记录。
        """
        return self._repository.append_event(run_id, payload)
