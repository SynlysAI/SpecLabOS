"""系统健康检查接口路由。"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict:
    """返回服务存活状态,供 Plane 等外部平台健康探测调用。

    Returns:
        包含服务标识与状态的最小 JSON 对象。
    """
    return {"status": "ok", "service": "speclabos"}
