"""SmartDataHub 接口认证测试。"""

import pytest
from fastapi import HTTPException

from app.api.routes.data_assets import require_datahub_auth
from app.core.config import get_settings


@pytest.fixture
def auth_enabled(monkeypatch):
    """启用认证并注入互不相同的两类令牌。"""
    monkeypatch.setattr(get_settings().auth, "enabled", True)
    monkeypatch.setattr(get_settings().datahub, "api_token", "datahub-token")
    monkeypatch.setattr(get_settings().external_api, "api_token", "unified-token")


def test_datahub_token_accepted(auth_enabled):
    """SmartDataHub 专属令牌应通过校验。"""
    assert require_datahub_auth("Bearer datahub-token") is None


def test_unified_external_token_accepted(auth_enabled):
    """统一外部 API Token 应同样通过校验。"""
    assert require_datahub_auth("Bearer unified-token") is None


def test_invalid_token_rejected(auth_enabled):
    """无法识别的凭证应返回 401。"""
    with pytest.raises(HTTPException) as excinfo:
        require_datahub_auth("Bearer wrong-token")
    assert excinfo.value.status_code == 401


def test_missing_token_rejected(auth_enabled):
    """未提供认证信息应返回 401。"""
    with pytest.raises(HTTPException) as excinfo:
        require_datahub_auth(None)
    assert excinfo.value.status_code == 401
