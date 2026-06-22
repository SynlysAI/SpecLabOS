"""SmartAccess 服务测试。"""

import pytest

from app.repositories.smartaccess_repository import SmartAccessRepository
from app.schemas.smartaccess import (
    SmartAccessRunCreateRequest,
    SmartAccessRunEventRequest,
    SmartAccessTemplatePublishRequest,
)
from app.services.smartaccess_service import SmartAccessService


class FakePublisher:
    """记录 SmartAccess 任务消息的测试发布器。"""

    def __init__(self) -> None:
        """初始化发布器。"""
        self.messages = []

    def publish_run_requested(self, payload: dict) -> None:
        """记录远程运行请求消息。

        Args:
            payload: 运行请求消息。
        """
        self.messages.append(payload)


def _workflow_payload() -> dict:
    """构造最小 SmartAccess workflow 快照。

    Returns:
        workflow 字典。
    """
    return {
        "metadata": {
            "workflow_id": "wf_weixin",
            "template_id": "tpl_weixin",
            "template_version": "1.0.0",
            "anchor_profile": "weixin",
        },
        "steps": [
            {"id": "open", "anchor_id": "open", "action": "click"},
            {"id": "observe", "anchor_id": "status", "action": "observe"},
        ],
    }


def test_publish_template_upserts_snapshot(fake_database) -> None:
    """验证模板发布会写入模板快照。"""
    service = SmartAccessService(
        repository=SmartAccessRepository(fake_database),
        publisher=FakePublisher(),
    )

    record = service.publish_template(
        SmartAccessTemplatePublishRequest(
            template_id="tpl_weixin",
            template_version="1.0.0",
            workflow_id="wf_weixin",
            name="微信流程",
            anchor_profile="weixin",
            source_device_id="weixin",
            published_by="smartaccess",
            workflow=_workflow_payload(),
        )
    )

    assert record["template_id"] == "tpl_weixin"
    assert record["template_version"] == "1.0.0"
    assert record["step_count"] == 2
    assert fake_database["smartaccess_templates"].count_documents({}) == 1


def test_create_run_publishes_device_message(fake_database) -> None:
    """验证创建运行会写入运行记录并发布设备消息。"""
    publisher = FakePublisher()
    service = SmartAccessService(
        repository=SmartAccessRepository(fake_database),
        publisher=publisher,
    )
    service.publish_template(
        SmartAccessTemplatePublishRequest(
            template_id="tpl_weixin",
            template_version="1.0.0",
            workflow_id="wf_weixin",
            name="微信流程",
            anchor_profile="weixin",
            source_device_id="weixin",
            published_by="smartaccess",
            workflow=_workflow_payload(),
        )
    )

    run = service.create_run(
        SmartAccessRunCreateRequest(
            template_id="tpl_weixin",
            template_version="1.0.0",
            device_id="weixin",
            requested_by="admin",
        )
    )

    assert run["status"] == "queued"
    assert run["device_id"] == "weixin"
    assert publisher.messages[0]["run_id"] == run["run_id"]
    assert publisher.messages[0]["workflow"]["metadata"]["workflow_id"] == "wf_weixin"


def test_append_event_updates_run_status(fake_database) -> None:
    """验证事件回传会推进运行状态。"""
    service = SmartAccessService(
        repository=SmartAccessRepository(fake_database),
        publisher=FakePublisher(),
    )
    service.publish_template(
        SmartAccessTemplatePublishRequest(
            template_id="tpl_weixin",
            template_version="1.0.0",
            workflow_id="wf_weixin",
            name="微信流程",
            anchor_profile="weixin",
            source_device_id="weixin",
            published_by="smartaccess",
            workflow=_workflow_payload(),
        )
    )
    run = service.create_run(
        SmartAccessRunCreateRequest(
            template_id="tpl_weixin",
            template_version="1.0.0",
            device_id="weixin",
            requested_by="admin",
        )
    )

    service.append_event(
        run["run_id"],
        SmartAccessRunEventRequest(
            event_id="evt-1",
            event_type="run.started",
            status="running",
            payload={},
        ),
    )

    stored = fake_database["smartaccess_runs"].find_one({"run_id": run["run_id"]})
    assert stored["status"] == "running"
