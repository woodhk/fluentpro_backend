"""
Redis Streams client wrapper for event bus infrastructure
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import redis.asyncio as redis
from redis.exceptions import ResponseError
import json
import time

logger = logging.getLogger(__name__)

@dataclass
class StreamMessage:
    """Represents a message from Redis Stream"""
    message_id: str
    stream_name: str
    data: Dict[str, Any]
    timestamp: float

class RedisStreamsClient:
    """Redis Streams client for reliable event processing"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize Redis Streams client
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._redis_pool = None
        self._redis = None
        
    async def connect(self) -> None:
        """Establish Redis connection"""
        try:
            self._redis_pool = redis.ConnectionPool.from_url(self.redis_url)
            self._redis = redis.Redis(connection_pool=self._redis_pool)
            
            # Test connection
            await self._redis.ping()
            logger.info("Redis Streams client connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
        if self._redis_pool:
            await self._redis_pool.disconnect()
        logger.info("Redis Streams client disconnected")
    
    async def add_to_stream(
        self,
        stream_name: str,
        data: Dict[str, Any],
        message_id: str = "*",
        maxlen: Optional[int] = None
    ) -> str:
        """
        Add message to Redis Stream
        
        Args:
            stream_name: Name of the stream
            data: Message data as dictionary
            message_id: Message ID (default "*" for auto-generation)
            maxlen: Maximum stream length (for trimming)
            
        Returns:
            Generated message ID
        """
        try:
            # Serialize data to JSON strings
            serialized_data = {
                key: json.dumps(value) if not isinstance(value, str) else value
                for key, value in data.items()
            }
            
            result = await self._redis.xadd(
                stream_name,
                serialized_data,
                id=message_id,
                maxlen=maxlen
            )
            
            logger.debug(f"Added message {result} to stream {stream_name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to add message to stream {stream_name}: {e}")
            raise
    
    async def create_consumer_group(
        self,
        stream_name: str,
        group_name: str,
        start_id: str = "0"
    ) -> bool:
        """
        Create consumer group for stream
        
        Args:
            stream_name: Name of the stream
            group_name: Name of the consumer group
            start_id: Starting message ID (0 for all messages, $ for new messages)
            
        Returns:
            True if group was created, False if already exists
        """
        try:
            await self._redis.xgroup_create(
                stream_name,
                group_name,
                id=start_id,
                mkstream=True  # Create stream if it doesn't exist
            )
            logger.info(f"Created consumer group {group_name} for stream {stream_name}")
            return True
            
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group {group_name} already exists for stream {stream_name}")
                return False
            else:
                logger.error(f"Failed to create consumer group {group_name}: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to create consumer group {group_name}: {e}")
            raise
    
    async def read_from_stream(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        count: int = 1,
        block_ms: Optional[int] = 1000
    ) -> List[StreamMessage]:
        """
        Read messages from stream using consumer group
        
        Args:
            stream_name: Name of the stream
            group_name: Name of the consumer group
            consumer_name: Name of the consumer
            count: Maximum number of messages to read
            block_ms: Block time in milliseconds (None for non-blocking)
            
        Returns:
            List of stream messages
        """
        try:
            result = await self._redis.xreadgroup(
                group_name,
                consumer_name,
                {stream_name: ">"},
                count=count,
                block=block_ms
            )
            
            messages = []
            for stream, stream_messages in result:
                for message_id, fields in stream_messages:
                    # Deserialize fields
                    data = {}
                    for key, value in fields.items():
                        try:
                            # Try to parse as JSON, fallback to string
                            data[key.decode()] = json.loads(value.decode())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            data[key.decode()] = value.decode()
                    
                    messages.append(StreamMessage(
                        message_id=message_id.decode(),
                        stream_name=stream.decode(),
                        data=data,
                        timestamp=time.time()
                    ))
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to read from stream {stream_name}: {e}")
            raise
    
    async def acknowledge_message(
        self,
        stream_name: str,
        group_name: str,
        message_id: str
    ) -> int:
        """
        Acknowledge processed message
        
        Args:
            stream_name: Name of the stream
            group_name: Name of the consumer group
            message_id: ID of the message to acknowledge
            
        Returns:
            Number of acknowledged messages
        """
        try:
            result = await self._redis.xack(stream_name, group_name, message_id)
            logger.debug(f"Acknowledged message {message_id} in stream {stream_name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to acknowledge message {message_id}: {e}")
            raise
    
    async def get_pending_messages(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending (unacknowledged) messages
        
        Args:
            stream_name: Name of the stream
            group_name: Name of the consumer group
            consumer_name: Specific consumer name (None for all consumers)
            
        Returns:
            List of pending message info
        """
        try:
            if consumer_name:
                result = await self._redis.xpending_range(
                    stream_name, group_name, "-", "+", count=100, consumername=consumer_name
                )
            else:
                result = await self._redis.xpending(stream_name, group_name)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get pending messages from stream {stream_name}: {e}")
            raise
    
    async def claim_pending_messages(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        min_idle_time_ms: int = 60000,  # 1 minute
        message_ids: Optional[List[str]] = None
    ) -> List[StreamMessage]:
        """
        Claim pending messages from other consumers
        
        Args:
            stream_name: Name of the stream
            group_name: Name of the consumer group
            consumer_name: Name of the claiming consumer
            min_idle_time_ms: Minimum idle time in milliseconds
            message_ids: Specific message IDs to claim (None for auto-discovery)
            
        Returns:
            List of claimed messages
        """
        try:
            if message_ids is None:
                # Auto-discover pending messages
                pending = await self.get_pending_messages(stream_name, group_name)
                if isinstance(pending, list) and pending:
                    message_ids = [msg[0] for msg in pending if msg[2] > min_idle_time_ms]
                else:
                    return []
            
            if not message_ids:
                return []
            
            result = await self._redis.xclaim(
                stream_name,
                group_name,
                consumer_name,
                min_idle_time_ms,
                message_ids
            )
            
            messages = []
            for message_id, fields in result:
                data = {}
                for key, value in fields.items():
                    try:
                        data[key.decode()] = json.loads(value.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        data[key.decode()] = value.decode()
                
                messages.append(StreamMessage(
                    message_id=message_id.decode(),
                    stream_name=stream_name,
                    data=data,
                    timestamp=time.time()
                ))
            
            logger.info(f"Claimed {len(messages)} messages from stream {stream_name}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to claim pending messages from stream {stream_name}: {e}")
            raise
    
    async def get_stream_info(self, stream_name: str) -> Dict[str, Any]:
        """
        Get information about a stream
        
        Args:
            stream_name: Name of the stream
            
        Returns:
            Stream information dictionary
        """
        try:
            result = await self._redis.xinfo_stream(stream_name)
            return result
        except Exception as e:
            logger.error(f"Failed to get stream info for {stream_name}: {e}")
            raise
    
    async def trim_stream(
        self,
        stream_name: str,
        maxlen: int,
        approximate: bool = True
    ) -> int:
        """
        Trim stream to maximum length
        
        Args:
            stream_name: Name of the stream
            maxlen: Maximum number of messages to keep
            approximate: Whether to use approximate trimming for performance
            
        Returns:
            Number of messages removed
        """
        try:
            result = await self._redis.xtrim(
                stream_name,
                maxlen=maxlen,
                approximate=approximate
            )
            logger.info(f"Trimmed stream {stream_name} to {maxlen} messages, removed {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to trim stream {stream_name}: {e}")
            raise
    
    async def delete_consumer(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str
    ) -> int:
        """
        Delete a consumer from a consumer group
        
        Args:
            stream_name: Name of the stream
            group_name: Name of the consumer group
            consumer_name: Name of the consumer to delete
            
        Returns:
            Number of pending messages that were reassigned
        """
        try:
            result = await self._redis.xgroup_delconsumer(
                stream_name, group_name, consumer_name
            )
            logger.info(f"Deleted consumer {consumer_name} from group {group_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete consumer {consumer_name}: {e}")
            raise
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected to Redis"""
        return self._redis is not None