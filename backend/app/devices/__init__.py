"""设备模块。"""


def load_builtin_devices() -> None:
    """导入内置设备模块，触发装饰器注册。"""
    from app.devices import nmr_device  # noqa: F401
    from app.devices import pi_device  # noqa: F401
    from app.devices import gpc_device  # noqa: F401
    from app.devices import ir_device  # noqa: F401
    from app.devices import raman_device  # noqa: F401
    from app.devices import lcms_device  # noqa: F401
    from app.devices import resin_device  # noqa: F401
    from app.devices import station_device  # noqa: F401
