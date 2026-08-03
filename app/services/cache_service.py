import hashlib
import json
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from ..db.models import TaskStatus
from ..schemas.task import TaskRead

logger = logging.getLogger("taskhub.cache")


class TaskListCache:
    KEY_PREFIX = "taskhub:projects"

    def __init__(self, redis: Redis | None, ttl_seconds: int) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @classmethod
    def _key(
        cls,
        project_id: str,
        *,
        status: TaskStatus | None,
        priority: int | None,
        assignee_id: str | None,
        page: int,
        limit: int,
    ) -> str:
        query = json.dumps(
            {
                "assignee_id": assignee_id,
                "limit": limit,
                "page": page,
                "priority": priority,
                "status": status.value if status else None,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:20]
        return f"{cls.KEY_PREFIX}:{project_id}:tasks:{query_hash}"

    async def get(
        self,
        project_id: str,
        *,
        status: TaskStatus | None,
        priority: int | None,
        assignee_id: str | None,
        page: int,
        limit: int,
    ) -> list[TaskRead] | None:
        if not self.redis:
            return None

        key = self._key(
            project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            page=page,
            limit=limit,
        )
        try:
            cached = await self.redis.get(key)
        except RedisError:
            logger.exception("cache_read_failed key=%s", key)
            return None

        if cached is None:
            logger.debug("cache_miss key=%s", key)
            return None

        try:
            items = json.loads(cached)
            result = [TaskRead.model_validate(item) for item in items]
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.exception("cache_decode_failed key=%s", key)
            await self._delete_key(key)
            return None

        logger.debug("cache_hit key=%s", key)
        return result

    async def set(
        self,
        project_id: str,
        tasks: list[TaskRead],
        *,
        status: TaskStatus | None,
        priority: int | None,
        assignee_id: str | None,
        page: int,
        limit: int,
    ) -> None:
        if not self.redis or self.ttl_seconds <= 0:
            return

        key = self._key(
            project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            page=page,
            limit=limit,
        )
        payload = json.dumps(
            [task.model_dump(mode="json") for task in tasks],
            separators=(",", ":"),
        )
        try:
            await self.redis.set(key, payload, ex=self.ttl_seconds)
        except RedisError:
            logger.exception("cache_write_failed key=%s", key)

    async def invalidate_project(self, project_id: str) -> None:
        if not self.redis:
            return

        pattern = f"{self.KEY_PREFIX}:{project_id}:tasks:*"
        try:
            keys = [key async for key in self.redis.scan_iter(match=pattern, count=100)]
            if keys:
                await self.redis.delete(*keys)
            logger.info("cache_invalidated project_id=%s key_count=%s", project_id, len(keys))
        except RedisError:
            logger.exception("cache_invalidation_failed project_id=%s", project_id)

    async def _delete_key(self, key: str) -> None:
        if not self.redis:
            return
        try:
            await self.redis.delete(key)
        except RedisError:
            logger.exception("cache_delete_failed key=%s", key)
