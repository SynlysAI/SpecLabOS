"""SmartAccess RabbitMQ 发布器。"""

import json
from collections.abc import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel


class SmartAccessNullPublisher:
    """测试和未配置 MQ 时使用的空发布器。"""

    def publish_run_requested(self, payload: dict) -> None:
        """忽略远程运行请求消息。

        Args:
            payload: 运行请求消息。
        """
        return None


class SmartAccessRabbitMQPublisher:
    """SmartAccess 远程运行 RabbitMQ 发布器。"""

    def __init__(self, channel_factory: Callable[[], BlockingChannel]) -> None:
        """初始化发布器。

        Args:
            channel_factory: RabbitMQ channel 工厂。
        """
        self._channel_factory = channel_factory

    def publish_run_requested(self, payload: dict) -> None:
        """发布 SmartAccess 远程运行请求。

        Args:
            payload: 运行请求消息。
        """
        device_id = str(payload["device_id"])
        routing_key = f"device.{device_id}.run.requested"
        channel = self._channel_factory()
        channel.exchange_declare(
            exchange="smartaccess.commands",
            exchange_type="topic",
            durable=True,
        )
        channel.basic_publish(
            exchange="smartaccess.commands",
            routing_key=routing_key,
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            ),
        )
