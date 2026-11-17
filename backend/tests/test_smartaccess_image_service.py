"""SmartAccess 设备图片服务测试。"""

import pytest
from fastapi import HTTPException

from app.core.config import get_settings
from app.domain.device import DeviceResource
from app.repositories.smartaccess_image_repository import (
    SmartAccessImageRepository,
)
from app.services.device_service import DeviceService
from app.services.smartaccess_device_service import SmartAccessDeviceService
from app.services.smartaccess_image_service import SmartAccessImageService


class FakeTemplateService:
    """提供固定已发布模板的测试服务。"""

    @staticmethod
    def list_templates(status: str | None = None) -> list[dict]:
        """返回一条已发布模板。

        Args:
            status: 模板状态过滤条件。

        Returns:
            模板记录列表。
        """
        return [
            {
                "template_id": "tpl_ccswitch",
                "template_version": "1.0.0",
                "source_device_id": "pc-workstation",
                "anchor_profile": "CCswitch软件",
                "status": "published",
                "step_count": 2,
            }
        ]

    @staticmethod
    def list_runs() -> list[dict]:
        """返回空运行列表。

        Returns:
            运行记录列表。
        """
        return []


class FakeImageService:
    """提供固定设备图片地址的测试服务。"""

    @staticmethod
    def list_image_urls() -> dict[str, str]:
        """返回执行端到图片地址的映射。

        Returns:
            图片地址映射。
        """
        return {
            "pc-workstation": (
                "/api/device-images/smartaccess-device-abc123?v=deadbeef"
            )
        }


def test_save_image_writes_file_and_returns_url(fake_database, tmp_path, monkeypatch) -> None:
    """验证设备图片会写入目录并生成带版本号的访问地址。"""
    monkeypatch.setattr(get_settings().device_images, "image_dir", str(tmp_path))
    service = SmartAccessImageService(SmartAccessImageRepository(fake_database))

    record = service.save_image(
        "pc-workstation",
        "device.png",
        "image/png",
        b"fake-png-content",
    )

    assert record["source_device_id"] == "pc-workstation"
    assert (tmp_path / record["storage_name"]).read_bytes() == b"fake-png-content"
    assert record["image_url"].startswith(
        "/api/device-images/smartaccess-device-"
    )
    assert "?v=" in record["image_url"]
    assert service.get_image_url("pc-workstation") == record["image_url"]
    assert service.list_image_urls() == {"pc-workstation": record["image_url"]}


def test_save_image_replaces_previous_file_with_other_extension(
    fake_database,
    tmp_path,
    monkeypatch,
) -> None:
    """验证更换图片格式后会清理旧文件。"""
    monkeypatch.setattr(get_settings().device_images, "image_dir", str(tmp_path))
    service = SmartAccessImageService(SmartAccessImageRepository(fake_database))

    first = service.save_image("pc-workstation", "device.png", "image/png", b"png")
    second = service.save_image("pc-workstation", "device.webp", "image/webp", b"webp")

    assert not (tmp_path / first["storage_name"]).exists()
    assert (tmp_path / second["storage_name"]).exists()
    assert second["storage_name"].endswith(".webp")


def test_save_image_rejects_unsupported_format(fake_database, tmp_path, monkeypatch) -> None:
    """验证不支持的图片格式会被拒绝。"""
    monkeypatch.setattr(get_settings().device_images, "image_dir", str(tmp_path))
    service = SmartAccessImageService(SmartAccessImageRepository(fake_database))

    with pytest.raises(HTTPException) as exc_info:
        service.save_image("pc-workstation", "device.txt", "text/plain", b"text")

    assert getattr(exc_info.value, "status_code", None) == 400


def test_smartaccess_device_carries_uploaded_image_url() -> None:
    """验证虚拟设备会带上执行端设备图片地址。"""
    service = SmartAccessDeviceService(
        smartaccess_service=FakeTemplateService(),
        image_service=FakeImageService(),
    )

    devices = service.list_devices()

    assert len(devices) == 1
    assert devices[0].device_id == "smartaccess:pc-workstation"
    assert devices[0].image_url == (
        "/api/device-images/smartaccess-device-abc123?v=deadbeef"
    )


def test_serialize_device_prefers_resource_image_url() -> None:
    """验证设备序列化优先使用资源自带的图片地址。"""
    device = DeviceResource(
        device_id="smartaccess:pc-workstation",
        name="CCswitch软件",
        category="SmartAccess 远程设备",
        device_type="SmartAccessDevice",
        image_url="/api/device-images/smartaccess-device-abc123?v=deadbeef",
    )

    serialized = DeviceService.serialize_device(device)

    assert serialized["image_url"] == (
        "/api/device-images/smartaccess-device-abc123?v=deadbeef"
    )
