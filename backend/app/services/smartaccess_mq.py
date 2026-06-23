"""SmartAccess RabbitMQ 发布器。"""


class SmartAccessNullPublisher:
    """测试和未配置 MQ 时使用的空发布器。"""

    def publish_run_requested(self, payload: dict) -> None:
        """忽略远程运行请求消息。

        Args:
            payload: 运行请求消息。
        """
        return None
