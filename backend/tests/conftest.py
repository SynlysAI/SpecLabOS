"""测试夹具定义。"""

import mongomock
import pytest


@pytest.fixture
def fake_database():
    """提供基于 mongomock 的 Mongo 数据库实例。"""
    client = mongomock.MongoClient()
    return client["spec_labos_test"]
