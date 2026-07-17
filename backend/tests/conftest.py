"""测试夹具定义。"""

import mongomock
import pytest

from app.api.routes import smartaccess, workflows
from app.core.config import get_settings
from app.repositories.smartaccess_repository import SmartAccessRepository
from app.services.smartaccess_service import SmartAccessService


@pytest.fixture(autouse=True)
def _disable_auth_by_default(monkeypatch):
    """默认关闭鉴权,避免旧测试因新增的登录依赖而 401。

    需要鉴权的测试可自行 monkeypatch.setattr(get_settings().auth, "enabled", True)。
    """
    monkeypatch.setattr(get_settings().auth, "enabled", False)


@pytest.fixture
def fake_database():
    """提供基于 mongomock 的 Mongo 数据库实例。"""
    client = mongomock.MongoClient()
    return client["spec_labos_test"]


class FakeSmartAccessPublisher:
    """记录 SmartAccess 发布消息的测试发布器。"""

    def __init__(self) -> None:
        """初始化消息列表。"""
        self.messages = []

    def publish_run_requested(self, payload: dict) -> None:
        """记录运行请求发布消息。

        Args:
            payload: SmartAccess 运行请求消息。
        """
        self.messages.append(payload)


@pytest.fixture
def fake_smartaccess_service(fake_database, monkeypatch):
    """为路由测试提供隔离的 SmartAccess 服务。

    Args:
        fake_database: mongomock 测试数据库。
        monkeypatch: pytest monkeypatch 夹具。

    Returns:
        使用 fake publisher 的 SmartAccess 服务实例。
    """
    service = SmartAccessService(
        repository=SmartAccessRepository(fake_database),
        publisher=FakeSmartAccessPublisher(),
    )
    monkeypatch.setattr(smartaccess, "get_smartaccess_service", lambda: service)
    monkeypatch.setattr(workflows, "get_smartaccess_service", lambda: service)
    return service
