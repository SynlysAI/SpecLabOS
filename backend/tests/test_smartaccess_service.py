"""SmartAccess 服务测试。"""

import json

import pytest
from fastapi import HTTPException

from app.repositories.data_asset_repository import DataAssetRepository
from app.repositories.smartaccess_repository import SmartAccessRepository
from app.schemas.smartaccess import (
    SmartAccessRunCreateRequest,
    SmartAccessRunEventRequest,
    SmartAccessTemplatePublishRequest,
)
from app.services.smartaccess_mq import SmartAccessRabbitMQPublisher
from app.services.smartaccess_service import SmartAccessService


class FakeChannel:
    """记录 RabbitMQ 发布调用的测试 channel。"""

    def __init__(self) -> None:
        """初始化 channel。"""
        self.declared = []
        self.bound = []
        self.published = []

    def exchange_declare(self, **kwargs) -> None:
        """记录 exchange 声明。"""
        self.declared.append(kwargs)

    def queue_declare(self, **kwargs) -> None:
        """记录队列声明（测试中不阻塞）。"""

    def queue_bind(self, **kwargs) -> None:
        """记录队列绑定。"""
        self.bound.append(kwargs)

    def basic_publish(self, **kwargs) -> None:
        """记录发布消息。"""
        self.published.append(kwargs)


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


def _workflow_payload(step_id: str = "open") -> dict:
    """构造最小 SmartAccess workflow 快照。

    Args:
        step_id: 首步骤 ID,用于区分不同执行端的模板内容。

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
            {"id": step_id, "anchor_id": "open", "action": "click"},
            {"id": "observe", "anchor_id": "status", "action": "observe"},
        ],
    }


def test_rabbitmq_publisher_routes_to_device_queue() -> None:
    """验证 RabbitMQ publisher 使用设备 routing key。"""
    channel = FakeChannel()
    publisher = SmartAccessRabbitMQPublisher(channel_factory=lambda: channel)

    publisher.publish_run_requested(
        {"smartaccess_node_id": "weixin", "run_id": "sa_run_1"}
    )

    assert channel.declared[0]["exchange"] == "smartaccess.commands"
    assert channel.declared[0]["exchange_type"] == "topic"
    assert channel.declared[0]["durable"] is True
    assert channel.bound[0]["routing_key"] == "device.weixin.run.requested"
    assert channel.published[0]["routing_key"] == "device.weixin.run.requested"
    assert channel.published[0]["exchange"] == "smartaccess.commands"
    assert json.loads(channel.published[0]["body"].decode("utf-8")) == {
        "smartaccess_node_id": "weixin",
        "run_id": "sa_run_1",
    }
    assert channel.published[0]["properties"].content_type == "application/json"
    assert channel.published[0]["properties"].delivery_mode == 2


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
            smartaccess_node_id="weixin",
            target_device_id="weixin",
            requested_by="admin",
        )
    )

    assert run["status"] == "queued"
    assert run["smartaccess_node_id"] == "weixin"
    assert publisher.messages[0]["run_id"] == run["run_id"]
    assert publisher.messages[0]["workflow"]["metadata"]["workflow_id"] == "wf_weixin"


def test_create_run_uses_template_of_selected_execution_node(fake_database) -> None:
    """验证同名同版本模板按执行端隔离时读取目标执行端的快照。"""
    publisher = FakePublisher()
    service = SmartAccessService(
        repository=SmartAccessRepository(fake_database),
        publisher=publisher,
    )
    service.publish_template(
        SmartAccessTemplatePublishRequest(
            template_id="tpl_shared",
            template_version="1.0.0",
            workflow_id="wf_shared",
            name="共享流程",
            anchor_profile="CCswitch软件",
            source_device_id="pc-workstation",
            published_by="smartaccess",
            workflow=_workflow_payload(step_id="pc-local"),
        )
    )
    service.publish_template(
        SmartAccessTemplatePublishRequest(
            template_id="tpl_shared",
            template_version="1.0.0",
            workflow_id="wf_shared",
            name="共享流程",
            anchor_profile="CCswitch软件",
            source_device_id="lab-pc-02",
            published_by="smartaccess",
            workflow=_workflow_payload(step_id="lab-remote"),
        )
    )
    # 让另一台执行端的模板成为最近更新记录,验证不会回退到它
    fake_database["smartaccess_templates"].update_one(
        {"source_device_id": "lab-pc-02"},
        {"$set": {"updated_at": "2999-01-01T00:00:00+00:00"}},
    )

    run = service.create_run(
        SmartAccessRunCreateRequest(
            template_id="tpl_shared",
            template_version="1.0.0",
            smartaccess_node_id="pc-workstation",
            target_device_id="CCswitch软件",
            requested_by="admin",
        )
    )

    assert run["smartaccess_node_id"] == "pc-workstation"
    assert run["workflow_snapshot"]["steps"][0]["id"] == "pc-local"
    assert publisher.messages[0]["workflow"]["steps"][0]["id"] == "pc-local"


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
            smartaccess_node_id="weixin",
            target_device_id="weixin",
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


def _ingest_file(
    data_repository: DataAssetRepository,
    *,
    filename: str,
    device_run_id: str = "",
    ingested_at: str | None = None,
) -> dict:
    """直接通过仓储写入一条数据文件记录。

    Args:
        data_repository: 数据资产仓储。
        filename: 文件名。
        device_run_id: 采集时打标的任务 ID；为空表示未绑定。
        ingested_at: 指定入库时间；为空时使用仓储当前时间。

    Returns:
        文件记录。
    """
    record = data_repository.create_file_asset(
        collector_id="pc-collector",
        device_id="CCswitch软件",
        data_type="result_data",
        asset_kind="file",
        asset_group_id=filename,
        root_name=filename,
        relative_path=filename,
        filename=filename,
        content_type="text/csv",
        file_size=16,
        file_hash=f"hash-{filename}",
        storage_bucket="speclabos-data",
        storage_key=f"ccswitch/{filename}",
        storage_uri=f"minio://speclabos-data/ccswitch/{filename}",
        metadata={"device_run_id": device_run_id} if device_run_id else {},
    )
    if ingested_at is not None:
        data_repository._files.update_one(
            {"file_id": record["file_id"]},
            {"$set": {"ingested_at": ingested_at}},
        )
    return record


def _publish_and_run(fake_database, publisher) -> dict:
    """发布模板并发起一次运行。

    Args:
        fake_database: mongomock 测试数据库。
        publisher: 测试发布器。

    Returns:
        运行记录。
    """
    service = SmartAccessService(
        repository=SmartAccessRepository(fake_database),
        publisher=publisher,
        data_repository=DataAssetRepository(fake_database),
    )
    service.publish_template(
        SmartAccessTemplatePublishRequest(
            template_id="tpl_ccswitch",
            template_version="1.0.0",
            workflow_id="wf_ccswitch",
            name="CCswitch流程",
            anchor_profile="CCswitch软件",
            source_device_id="pc-workstation",
            published_by="smartaccess",
            workflow=_workflow_payload(),
        )
    )
    return service.create_run(
        SmartAccessRunCreateRequest(
            template_id="tpl_ccswitch",
            template_version="1.0.0",
            smartaccess_node_id="pc-workstation",
            target_device_id="CCswitch软件",
            requested_by="admin",
        )
    )


def test_get_run_returns_bound_and_suggested_data_files(fake_database) -> None:
    """验证运行详情返回打标绑定的数据文件与时间窗建议关联。"""
    data_repository = DataAssetRepository(fake_database)
    publisher = FakePublisher()
    run = _publish_and_run(fake_database, publisher)
    service = SmartAccessService(
        repository=SmartAccessRepository(fake_database),
        publisher=publisher,
        data_repository=data_repository,
    )

    # 采集器打标绑定的文件 + 窗口内未打标文件 + 窗口外文件
    _ingest_file(data_repository, filename="bound.csv", device_run_id=run["run_id"])
    _ingest_file(data_repository, filename="suggest.csv")
    _ingest_file(
        data_repository,
        filename="old.csv",
        ingested_at="2020-01-01T00:00:00+00:00",
    )

    detail = service.get_run(run["run_id"])

    bound_names = {item["filename"] for item in detail["data_files"]}
    suggestion_names = {item["filename"] for item in detail["data_suggestions"]}
    assert bound_names == {"bound.csv"}
    assert suggestion_names == {"suggest.csv"}
    assert all(item["bound"] for item in detail["data_files"])
    assert all(not item["bound"] for item in detail["data_suggestions"])


def test_bind_data_file_confirms_suggestion(fake_database) -> None:
    """验证人工确认绑定后文件进入已绑定列表。"""
    data_repository = DataAssetRepository(fake_database)
    publisher = FakePublisher()
    run = _publish_and_run(fake_database, publisher)
    service = SmartAccessService(
        repository=SmartAccessRepository(fake_database),
        publisher=publisher,
        data_repository=data_repository,
    )
    record = _ingest_file(data_repository, filename="manual.csv")

    bound = service.bind_data_file(run["run_id"], record["file_id"])

    assert bound["bound"] is True
    detail = service.get_run(run["run_id"])
    assert {item["filename"] for item in detail["data_files"]} == {"manual.csv"}
    assert detail["data_suggestions"] == []


def test_bind_data_file_missing_file_raises_404(fake_database) -> None:
    """验证绑定不存在的文件返回 404。"""
    publisher = FakePublisher()
    run = _publish_and_run(fake_database, publisher)
    service = SmartAccessService(
        repository=SmartAccessRepository(fake_database),
        publisher=publisher,
        data_repository=DataAssetRepository(fake_database),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.bind_data_file(run["run_id"], "missing-file")

    assert getattr(exc_info.value, "status_code", None) == 404


def test_append_event_rejects_missing_run(fake_database) -> None:
    """验证不存在的运行不会接收事件回传。"""
    service = SmartAccessService(
        repository=SmartAccessRepository(fake_database),
        publisher=FakePublisher(),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.append_event(
            "missing-run",
            SmartAccessRunEventRequest(
                event_id="evt-missing-run",
                event_type="run.started",
                status="running",
                payload={},
            ),
        )

    assert getattr(exc_info.value, "status_code", None) == 404
    assert fake_database["smartaccess_run_events"].count_documents({}) == 0


def test_append_event_is_idempotent_per_run(fake_database) -> None:
    """验证不同运行可复用事件 ID 且只更新各自状态。"""
    service = SmartAccessService(
        repository=SmartAccessRepository(fake_database),
        publisher=FakePublisher(),
    )
    service.publish_template(
        SmartAccessTemplatePublishRequest(
            template_id="tpl_same_event",
            template_version="1.0.0",
            workflow_id="wf_weixin",
            name="微信流程",
            anchor_profile="weixin",
            source_device_id="weixin",
            published_by="smartaccess",
            workflow=_workflow_payload(),
        )
    )
    first_run = service.create_run(
        SmartAccessRunCreateRequest(
            template_id="tpl_same_event",
            template_version="1.0.0",
            smartaccess_node_id="weixin",
            target_device_id="weixin",
            requested_by="admin",
        )
    )
    second_run = service.create_run(
        SmartAccessRunCreateRequest(
            template_id="tpl_same_event",
            template_version="1.0.0",
            smartaccess_node_id="weixin",
            target_device_id="weixin",
            requested_by="admin",
        )
    )

    first_event = service.append_event(
        first_run["run_id"],
        SmartAccessRunEventRequest(
            event_id="evt-shared",
            event_type="run.started",
            status="running",
            payload={},
        ),
    )
    second_event = service.append_event(
        second_run["run_id"],
        SmartAccessRunEventRequest(
            event_id="evt-shared",
            event_type="run.completed",
            status="completed",
            payload={},
        ),
    )

    assert first_event["run_id"] == first_run["run_id"]
    assert second_event["run_id"] == second_run["run_id"]
    first_stored = fake_database["smartaccess_runs"].find_one(
        {"run_id": first_run["run_id"]}
    )
    second_stored = fake_database["smartaccess_runs"].find_one(
        {"run_id": second_run["run_id"]}
    )
    assert first_stored["status"] == "running"
    assert second_stored["status"] == "completed"
