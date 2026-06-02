import os
import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Set, Any
import redis.asyncio as aioredis
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class SSEService:
    def __init__(self):
        self.redis_client = None
        self._local_listeners: Dict[str, Set[asyncio.Queue]] = {}
        self._is_redis_available = False
        self._init_task = None

    def _get_init_task(self):
        if self._init_task is None:
            self._init_task = asyncio.create_task(self._initialize_redis())
        return self._init_task

    async def _initialize_redis(self):
        try:
            logger.info(f"SSE Service: Attempting to connect to Redis at {REDIS_URL}")
            self.redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
            # Ping to confirm connection
            await self.redis_client.ping()
            self._is_redis_available = True
            logger.info("SSE Service: Successfully initialized Redis Pub/Sub broker.")
        except Exception as e:
            logger.warning(f"SSE Service: Redis connection failed ({e}). Falling back to local in-memory event channels.")
            self.redis_client = None
            self._is_redis_available = False

    async def publish_event(self, job_id: str, event: Dict[str, Any]) -> None:
        """Publishes an event to a job's stream channel"""
        # Ensure initialization has completed
        init_task = self._get_init_task()
        if not init_task.done():
            await init_task

        event_str = json.dumps(event)
        
        # 1. Publish to Redis if available
        if self._is_redis_available and self.redis_client:
            try:
                channel = f"job_channel:{job_id}"
                await self.redis_client.publish(channel, event_str)
                return
            except Exception as e:
                logger.warning(f"SSE Service: Redis publish failed ({e}). Reverting to local fallback.")
                self._is_redis_available = False

        # 2. Local fallback publishing
        if job_id in self._local_listeners:
            closed_queues = set()
            for queue in self._local_listeners[job_id]:
                try:
                    queue.put_nowait(event_str)
                except Exception as ex:
                    # Queue might be full or closed
                    closed_queues.add(queue)
            
            # Clean up closed listeners
            self._local_listeners[job_id] -= closed_queues

    async def listen_events(self, job_id: str) -> AsyncGenerator[str, None]:
        """Subscribes and yields formatted Server-Sent Events (SSE)"""
        init_task = self._get_init_task()
        if not init_task.done():
            await init_task

        # Yield a start connection event
        yield f"event: connect\ndata: {json.dumps({'message': 'Connected to analysis stream'})}\n\n"

        # 1. Subscribe via Redis if available
        if self._is_redis_available and self.redis_client:
            try:
                channel = f"job_channel:{job_id}"
                pubsub = self.redis_client.pubsub()
                await pubsub.subscribe(channel)
                logger.info(f"SSE Service: Client subscribed to Redis channel '{channel}'")
                
                try:
                    while True:
                        # Listen with a timeout to allow for periodic keep-alive
                        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=2.0)
                        if message:
                            yield f"data: {message['data']}\n\n"
                        else:
                            # Send Keep-Alive ping to prevent proxy drops
                            yield ": keep-alive\n\n"
                finally:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                return
            except Exception as e:
                logger.warning(f"SSE Service: Redis subscribe failed ({e}). Reverting to local queue...")
                self._is_redis_available = False

        # 2. Local fallback queue subscription
        local_queue = asyncio.Queue(maxsize=100)
        if job_id not in self._local_listeners:
            self._local_listeners[job_id] = set()
        self._local_listeners[job_id].add(local_queue)
        
        logger.info(f"SSE Service: Client subscribed to Local Queue for job '{job_id}'")
        
        try:
            while True:
                try:
                    # Retrieve event with a timeout to allow for keep-alives
                    event_data = await asyncio.wait_for(local_queue.get(), timeout=2.0)
                    yield f"data: {event_data}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            if job_id in self._local_listeners:
                self._local_listeners[job_id].discard(local_queue)
                if not self._local_listeners[job_id]:
                    del self._local_listeners[job_id]
            logger.info(f"SSE Service: Unsubscribed Local Queue for job '{job_id}'")

# Global singleton
sse_service = SSEService()
