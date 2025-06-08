"""
State recovery and backup mechanisms for conversation state management.

Provides backup strategies, corruption detection, and recovery capabilities
to ensure conversation state resilience and data integrity.
"""

import asyncio
import json
import logging
import hashlib
import gzip
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as redis

from domains.shared.models.conversation_state import (
    ConversationState,
    ConversationMessage,
    ConversationContext,
    ConversationStatus,
    ConversationStateDelta
)

logger = logging.getLogger(__name__)


class BackupType(str, Enum):
    """Types of state backups"""
    FULL = "full"
    INCREMENTAL = "incremental"
    SNAPSHOT = "snapshot"


class RecoveryStatus(str, Enum):
    """Status of recovery operations"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    NOT_FOUND = "not_found"


@dataclass
class StateVersion:
    """Represents a version of conversation state"""
    version_id: str
    conversation_id: str
    version_number: int
    backup_type: BackupType
    created_at: datetime
    checksum: str
    size_bytes: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "version_id": self.version_id,
            "conversation_id": self.conversation_id,
            "version_number": self.version_number,
            "backup_type": self.backup_type.value,
            "created_at": self.created_at.isoformat(),
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateVersion":
        """Create from dictionary"""
        return cls(
            version_id=data["version_id"],
            conversation_id=data["conversation_id"],
            version_number=data["version_number"],
            backup_type=BackupType(data["backup_type"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            checksum=data["checksum"],
            size_bytes=data["size_bytes"],
            metadata=data.get("metadata", {})
        )


@dataclass
class BackupMetadata:
    """Metadata for backup operations"""
    backup_id: str
    conversation_id: str
    backup_type: BackupType
    created_at: datetime
    expires_at: Optional[datetime]
    compression: bool
    encryption: bool
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "backup_id": self.backup_id,
            "conversation_id": self.conversation_id,
            "backup_type": self.backup_type.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "compression": self.compression,
            "encryption": self.encryption,
            "tags": self.tags
        }


@dataclass
class RecoveryResult:
    """Result of a recovery operation"""
    status: RecoveryStatus
    recovered_state: Optional[ConversationState]
    version_restored: Optional[StateVersion]
    errors: List[str]
    warnings: List[str]
    recovery_time_ms: float
    
    def is_successful(self) -> bool:
        """Check if recovery was successful"""
        return self.status in [RecoveryStatus.SUCCESS, RecoveryStatus.PARTIAL]


class IStateBackupStrategy(ABC):
    """Interface for state backup strategies"""
    
    @abstractmethod
    async def create_backup(
        self,
        conversation_state: ConversationState,
        backup_type: BackupType = BackupType.FULL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateVersion:
        """Create a backup of conversation state"""
        pass
    
    @abstractmethod
    async def restore_backup(
        self,
        conversation_id: str,
        version_id: Optional[str] = None,
        version_number: Optional[int] = None
    ) -> RecoveryResult:
        """Restore conversation state from backup"""
        pass
    
    @abstractmethod
    async def list_versions(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[StateVersion]:
        """List available versions for a conversation"""
        pass
    
    @abstractmethod
    async def delete_version(
        self,
        conversation_id: str,
        version_id: str
    ) -> bool:
        """Delete a specific version"""
        pass
    
    @abstractmethod
    async def cleanup_expired_backups(self) -> int:
        """Clean up expired backups"""
        pass


class IStateCorruptionDetector(ABC):
    """Interface for state corruption detection"""
    
    @abstractmethod
    async def validate_state(
        self,
        conversation_state: ConversationState
    ) -> Tuple[bool, List[str]]:
        """
        Validate conversation state integrity
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass
    
    @abstractmethod
    async def detect_corruption(
        self,
        conversation_id: str,
        current_state: ConversationState,
        expected_checksum: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Detect if state has been corrupted
        
        Returns:
            Tuple of (is_corrupted, list_of_issues)
        """
        pass


class RedisStateBackupStrategy(IStateBackupStrategy):
    """Redis-based state backup strategy with versioning"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        backup_key_prefix: str = "backup:",
        version_key_prefix: str = "version:",
        max_versions_per_conversation: int = 50,
        default_ttl_days: int = 30
    ):
        """
        Initialize Redis backup strategy
        
        Args:
            redis_client: Redis client instance
            backup_key_prefix: Prefix for backup keys
            version_key_prefix: Prefix for version metadata keys
            max_versions_per_conversation: Maximum versions to keep per conversation
            default_ttl_days: Default TTL for backups in days
        """
        self.redis = redis_client
        self.backup_key_prefix = backup_key_prefix
        self.version_key_prefix = version_key_prefix
        self.max_versions = max_versions_per_conversation
        self.default_ttl_days = default_ttl_days
    
    def _get_backup_key(self, conversation_id: str, version_id: str) -> str:
        """Get Redis key for backup data"""
        return f"{self.backup_key_prefix}{conversation_id}:{version_id}"
    
    def _get_version_list_key(self, conversation_id: str) -> str:
        """Get Redis key for version list"""
        return f"{self.version_key_prefix}list:{conversation_id}"
    
    def _get_version_metadata_key(self, conversation_id: str, version_id: str) -> str:
        """Get Redis key for version metadata"""
        return f"{self.version_key_prefix}meta:{conversation_id}:{version_id}"
    
    def _calculate_checksum(self, data: str) -> str:
        """Calculate SHA-256 checksum of data"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _compress_data(self, data: str) -> bytes:
        """Compress data using gzip"""
        return gzip.compress(data.encode())
    
    def _decompress_data(self, compressed_data: bytes) -> str:
        """Decompress gzip data"""
        return gzip.decompress(compressed_data).decode()
    
    async def create_backup(
        self,
        conversation_state: ConversationState,
        backup_type: BackupType = BackupType.FULL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateVersion:
        """Create a backup of conversation state"""
        try:
            conversation_id = conversation_state.conversation_id
            version_id = f"v_{int(time.time() * 1000)}_{conversation_id[:8]}"
            
            # Get next version number
            version_number = await self._get_next_version_number(conversation_id)
            
            # Serialize state data
            state_data = json.dumps(conversation_state.dict(), default=str)
            checksum = self._calculate_checksum(state_data)
            
            # Compress data for storage efficiency
            compressed_data = self._compress_data(state_data)
            
            # Create version metadata
            version = StateVersion(
                version_id=version_id,
                conversation_id=conversation_id,
                version_number=version_number,
                backup_type=backup_type,
                created_at=datetime.utcnow(),
                checksum=checksum,
                size_bytes=len(compressed_data),
                metadata=metadata or {}
            )
            
            # Store backup data
            backup_key = self._get_backup_key(conversation_id, version_id)
            ttl_seconds = self.default_ttl_days * 24 * 3600
            
            await self.redis.setex(backup_key, ttl_seconds, compressed_data)
            
            # Store version metadata
            version_meta_key = self._get_version_metadata_key(conversation_id, version_id)
            await self.redis.setex(
                version_meta_key,
                ttl_seconds,
                json.dumps(version.to_dict())
            )
            
            # Add to version list (sorted set by version number)
            version_list_key = self._get_version_list_key(conversation_id)
            await self.redis.zadd(version_list_key, {version_id: version_number})
            await self.redis.expire(version_list_key, ttl_seconds)
            
            # Cleanup old versions if needed
            await self._cleanup_old_versions(conversation_id)
            
            logger.info(
                f"Created backup {version_id} for conversation {conversation_id} "
                f"(type: {backup_type}, size: {len(compressed_data)} bytes)"
            )
            
            return version
            
        except Exception as e:
            logger.error(f"Failed to create backup for conversation {conversation_id}: {e}")
            raise
    
    async def restore_backup(
        self,
        conversation_id: str,
        version_id: Optional[str] = None,
        version_number: Optional[int] = None
    ) -> RecoveryResult:
        """Restore conversation state from backup"""
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            # Find version to restore
            if version_id is None and version_number is not None:
                version_id = await self._find_version_by_number(conversation_id, version_number)
            elif version_id is None:
                # Get latest version
                version_id = await self._get_latest_version_id(conversation_id)
            
            if not version_id:
                return RecoveryResult(
                    status=RecoveryStatus.NOT_FOUND,
                    recovered_state=None,
                    version_restored=None,
                    errors=["No backup version found"],
                    warnings=[],
                    recovery_time_ms=(time.time() - start_time) * 1000
                )
            
            # Get version metadata
            version_meta_key = self._get_version_metadata_key(conversation_id, version_id)
            version_meta_data = await self.redis.get(version_meta_key)
            
            if not version_meta_data:
                return RecoveryResult(
                    status=RecoveryStatus.NOT_FOUND,
                    recovered_state=None,
                    version_restored=None,
                    errors=[f"Version metadata not found for {version_id}"],
                    warnings=[],
                    recovery_time_ms=(time.time() - start_time) * 1000
                )
            
            version = StateVersion.from_dict(json.loads(version_meta_data))
            
            # Get backup data
            backup_key = self._get_backup_key(conversation_id, version_id)
            compressed_data = await self.redis.get(backup_key)
            
            if not compressed_data:
                return RecoveryResult(
                    status=RecoveryStatus.NOT_FOUND,
                    recovered_state=None,
                    version_restored=version,
                    errors=[f"Backup data not found for {version_id}"],
                    warnings=[],
                    recovery_time_ms=(time.time() - start_time) * 1000
                )
            
            # Decompress and deserialize
            state_data = self._decompress_data(compressed_data)
            
            # Verify checksum
            actual_checksum = self._calculate_checksum(state_data)
            if actual_checksum != version.checksum:
                warnings.append(f"Checksum mismatch: expected {version.checksum}, got {actual_checksum}")
            
            # Restore conversation state
            state_dict = json.loads(state_data)
            recovered_state = ConversationState.parse_obj(state_dict)
            
            recovery_time_ms = (time.time() - start_time) * 1000
            
            status = RecoveryStatus.SUCCESS
            if warnings:
                status = RecoveryStatus.PARTIAL
            
            logger.info(
                f"Successfully restored conversation {conversation_id} from version {version_id} "
                f"in {recovery_time_ms:.2f}ms"
            )
            
            return RecoveryResult(
                status=status,
                recovered_state=recovered_state,
                version_restored=version,
                errors=errors,
                warnings=warnings,
                recovery_time_ms=recovery_time_ms
            )
            
        except Exception as e:
            error_msg = f"Failed to restore backup: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            return RecoveryResult(
                status=RecoveryStatus.FAILED,
                recovered_state=None,
                version_restored=None,
                errors=errors,
                warnings=warnings,
                recovery_time_ms=(time.time() - start_time) * 1000
            )
    
    async def list_versions(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[StateVersion]:
        """List available versions for a conversation"""
        try:
            version_list_key = self._get_version_list_key(conversation_id)
            
            # Get version IDs sorted by version number (most recent first)
            version_ids = await self.redis.zrevrange(version_list_key, 0, limit - 1)
            
            versions = []
            for version_id in version_ids:
                if isinstance(version_id, bytes):
                    version_id = version_id.decode()
                
                # Get version metadata
                version_meta_key = self._get_version_metadata_key(conversation_id, version_id)
                version_meta_data = await self.redis.get(version_meta_key)
                
                if version_meta_data:
                    try:
                        version = StateVersion.from_dict(json.loads(version_meta_data))
                        versions.append(version)
                    except Exception as e:
                        logger.warning(f"Failed to parse version metadata for {version_id}: {e}")
            
            return versions
            
        except Exception as e:
            logger.error(f"Failed to list versions for conversation {conversation_id}: {e}")
            return []
    
    async def delete_version(
        self,
        conversation_id: str,
        version_id: str
    ) -> bool:
        """Delete a specific version"""
        try:
            backup_key = self._get_backup_key(conversation_id, version_id)
            version_meta_key = self._get_version_metadata_key(conversation_id, version_id)
            version_list_key = self._get_version_list_key(conversation_id)
            
            # Delete backup data, metadata, and remove from version list
            backup_deleted = await self.redis.delete(backup_key)
            meta_deleted = await self.redis.delete(version_meta_key)
            await self.redis.zrem(version_list_key, version_id)
            
            if backup_deleted > 0 or meta_deleted > 0:
                logger.info(f"Deleted version {version_id} for conversation {conversation_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete version {version_id}: {e}")
            return False
    
    async def cleanup_expired_backups(self) -> int:
        """Clean up expired backups"""
        try:
            # Redis TTL handles most cleanup automatically
            # This method could be extended for more complex cleanup logic
            cleanup_count = 0
            
            # Scan for version list keys
            pattern = f"{self.version_key_prefix}list:*"
            async for key in self.redis.scan_iter(match=pattern, count=100):
                key_str = key.decode() if isinstance(key, bytes) else key
                conversation_id = key_str[len(f"{self.version_key_prefix}list:"):]
                
                # Clean up old versions beyond max limit
                cleanup_count += await self._cleanup_old_versions(conversation_id)
            
            logger.info(f"Cleaned up {cleanup_count} expired backup versions")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired backups: {e}")
            return 0
    
    async def _get_next_version_number(self, conversation_id: str) -> int:
        """Get next version number for conversation"""
        try:
            version_list_key = self._get_version_list_key(conversation_id)
            
            # Get highest version number
            latest = await self.redis.zrevrange(version_list_key, 0, 0, withscores=True)
            
            if latest:
                return int(latest[0][1]) + 1
            else:
                return 1
                
        except Exception:
            return 1
    
    async def _find_version_by_number(self, conversation_id: str, version_number: int) -> Optional[str]:
        """Find version ID by version number"""
        try:
            version_list_key = self._get_version_list_key(conversation_id)
            
            # Get version ID with specific score (version number)
            result = await self.redis.zrangebyscore(
                version_list_key, 
                version_number, 
                version_number,
                start=0,
                num=1
            )
            
            if result:
                return result[0].decode() if isinstance(result[0], bytes) else result[0]
            return None
            
        except Exception:
            return None
    
    async def _get_latest_version_id(self, conversation_id: str) -> Optional[str]:
        """Get latest version ID for conversation"""
        try:
            version_list_key = self._get_version_list_key(conversation_id)
            
            # Get highest scoring member (latest version)
            result = await self.redis.zrevrange(version_list_key, 0, 0)
            
            if result:
                return result[0].decode() if isinstance(result[0], bytes) else result[0]
            return None
            
        except Exception:
            return None
    
    async def _cleanup_old_versions(self, conversation_id: str) -> int:
        """Clean up old versions beyond max limit"""
        try:
            version_list_key = self._get_version_list_key(conversation_id)
            
            # Get total count
            total_count = await self.redis.zcard(version_list_key)
            
            if total_count <= self.max_versions:
                return 0
            
            # Get old versions to delete (keep most recent max_versions)
            old_versions = await self.redis.zrange(
                version_list_key, 
                0, 
                total_count - self.max_versions - 1
            )
            
            cleanup_count = 0
            for version_id in old_versions:
                if isinstance(version_id, bytes):
                    version_id = version_id.decode()
                
                # Delete version
                if await self.delete_version(conversation_id, version_id):
                    cleanup_count += 1
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old versions for {conversation_id}: {e}")
            return 0


class BasicStateCorruptionDetector(IStateCorruptionDetector):
    """Basic state corruption detector with validation rules"""
    
    async def validate_state(
        self,
        conversation_state: ConversationState
    ) -> Tuple[bool, List[str]]:
        """Validate conversation state integrity"""
        errors = []
        
        try:
            # Basic structure validation
            if not conversation_state.conversation_id:
                errors.append("Missing conversation_id")
            
            if not conversation_state.user_id:
                errors.append("Missing user_id")
            
            # Validate timestamps
            if conversation_state.created_at > datetime.utcnow():
                errors.append("created_at is in the future")
            
            if conversation_state.updated_at < conversation_state.created_at:
                errors.append("updated_at is before created_at")
            
            # Validate messages
            for i, message in enumerate(conversation_state.messages):
                if not message.message_id:
                    errors.append(f"Message {i} missing message_id")
                
                if not message.content.strip():
                    errors.append(f"Message {i} has empty content")
                
                if message.timestamp > datetime.utcnow():
                    errors.append(f"Message {i} timestamp is in the future")
            
            # Validate token count consistency
            calculated_tokens = sum(
                msg.tokens_used or 0 for msg in conversation_state.messages
            )
            if abs(calculated_tokens - conversation_state.total_tokens_used) > 10:
                errors.append(
                    f"Token count mismatch: calculated {calculated_tokens}, "
                    f"stored {conversation_state.total_tokens_used}"
                )
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return False, errors
    
    async def detect_corruption(
        self,
        conversation_id: str,
        current_state: ConversationState,
        expected_checksum: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """Detect if state has been corrupted"""
        issues = []
        
        try:
            # Validate basic structure
            is_valid, validation_errors = await self.validate_state(current_state)
            if not is_valid:
                issues.extend(validation_errors)
            
            # Check checksum if provided
            if expected_checksum:
                state_data = json.dumps(current_state.dict(), default=str, sort_keys=True)
                actual_checksum = hashlib.sha256(state_data.encode()).hexdigest()
                
                if actual_checksum != expected_checksum:
                    issues.append(f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}")
            
            # Check for data anomalies
            if len(current_state.messages) > 10000:
                issues.append("Unusually high message count")
            
            if current_state.total_tokens_used > 1000000:
                issues.append("Unusually high token count")
            
            return len(issues) > 0, issues
            
        except Exception as e:
            issues.append(f"Corruption detection error: {e}")
            return True, issues


class StateRecoveryManager:
    """
    Main state recovery manager that coordinates backup, corruption detection, and recovery.
    
    Provides high-level operations for state backup and recovery with automatic
    corruption detection and fallback mechanisms.
    """
    
    def __init__(
        self,
        backup_strategy: IStateBackupStrategy,
        corruption_detector: IStateCorruptionDetector,
        auto_backup_interval: int = 300,  # 5 minutes
        max_recovery_attempts: int = 3
    ):
        """
        Initialize state recovery manager
        
        Args:
            backup_strategy: Backup strategy implementation
            corruption_detector: Corruption detector implementation
            auto_backup_interval: Automatic backup interval in seconds
            max_recovery_attempts: Maximum recovery attempts before giving up
        """
        self.backup_strategy = backup_strategy
        self.corruption_detector = corruption_detector
        self.auto_backup_interval = auto_backup_interval
        self.max_recovery_attempts = max_recovery_attempts
        self._backup_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_checkpoint(
        self,
        conversation_state: ConversationState,
        backup_type: BackupType = BackupType.FULL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateVersion:
        """Create a checkpoint (backup) of conversation state"""
        try:
            # Validate state before backup
            is_valid, errors = await self.corruption_detector.validate_state(conversation_state)
            
            if not is_valid:
                logger.warning(f"Creating backup of potentially invalid state: {errors}")
                if not metadata:
                    metadata = {}
                metadata["validation_errors"] = errors
            
            # Create backup
            version = await self.backup_strategy.create_backup(
                conversation_state, backup_type, metadata
            )
            
            logger.info(f"Created checkpoint {version.version_id} for conversation {conversation_state.conversation_id}")
            return version
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            raise
    
    async def recover_state(
        self,
        conversation_id: str,
        target_version: Optional[Union[str, int]] = None,
        validate_recovery: bool = True
    ) -> RecoveryResult:
        """
        Recover conversation state from backup
        
        Args:
            conversation_id: ID of conversation to recover
            target_version: Specific version ID or number to recover (None for latest)
            validate_recovery: Whether to validate recovered state
            
        Returns:
            Recovery result with status and recovered state
        """
        try:
            # Determine version parameters
            version_id = None
            version_number = None
            
            if isinstance(target_version, str):
                version_id = target_version
            elif isinstance(target_version, int):
                version_number = target_version
            
            # Attempt recovery
            for attempt in range(self.max_recovery_attempts):
                logger.info(f"Recovery attempt {attempt + 1} for conversation {conversation_id}")
                
                result = await self.backup_strategy.restore_backup(
                    conversation_id, version_id, version_number
                )
                
                if not result.is_successful():
                    logger.warning(f"Recovery attempt {attempt + 1} failed: {result.errors}")
                    continue
                
                # Validate recovered state if requested
                if validate_recovery and result.recovered_state:
                    is_valid, validation_errors = await self.corruption_detector.validate_state(
                        result.recovered_state
                    )
                    
                    if not is_valid:
                        result.warnings.extend(validation_errors)
                        logger.warning(f"Recovered state has validation issues: {validation_errors}")
                    
                    # Check for corruption
                    is_corrupted, corruption_issues = await self.corruption_detector.detect_corruption(
                        conversation_id, result.recovered_state
                    )
                    
                    if is_corrupted:
                        result.warnings.extend(corruption_issues)
                        logger.warning(f"Recovered state may be corrupted: {corruption_issues}")
                
                return result
            
            # All recovery attempts failed
            return RecoveryResult(
                status=RecoveryStatus.FAILED,
                recovered_state=None,
                version_restored=None,
                errors=[f"All {self.max_recovery_attempts} recovery attempts failed"],
                warnings=[],
                recovery_time_ms=0
            )
            
        except Exception as e:
            logger.error(f"Failed to recover state for conversation {conversation_id}: {e}")
            return RecoveryResult(
                status=RecoveryStatus.FAILED,
                recovered_state=None,
                version_restored=None,
                errors=[f"Recovery failed: {e}"],
                warnings=[],
                recovery_time_ms=0
            )
    
    async def rollback_to_version(
        self,
        conversation_id: str,
        target_version: Union[str, int]
    ) -> RecoveryResult:
        """
        Rollback conversation state to a specific version
        
        Args:
            conversation_id: ID of conversation to rollback
            target_version: Version ID or number to rollback to
            
        Returns:
            Recovery result with rollback status
        """
        logger.info(f"Rolling back conversation {conversation_id} to version {target_version}")
        
        # Create a backup of current state before rollback
        try:
            # Note: This would require getting current state from the state manager
            # For now, we'll just perform the recovery
            result = await self.recover_state(conversation_id, target_version, validate_recovery=True)
            
            if result.is_successful():
                logger.info(f"Successfully rolled back conversation {conversation_id} to version {target_version}")
            else:
                logger.error(f"Failed to rollback conversation {conversation_id}: {result.errors}")
            
            return result
            
        except Exception as e:
            logger.error(f"Rollback failed for conversation {conversation_id}: {e}")
            return RecoveryResult(
                status=RecoveryStatus.FAILED,
                recovered_state=None,
                version_restored=None,
                errors=[f"Rollback failed: {e}"],
                warnings=[],
                recovery_time_ms=0
            )
    
    async def get_version_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[StateVersion]:
        """Get version history for a conversation"""
        try:
            return await self.backup_strategy.list_versions(conversation_id, limit)
        except Exception as e:
            logger.error(f"Failed to get version history for {conversation_id}: {e}")
            return []
    
    async def start_auto_backup(
        self,
        conversation_id: str,
        backup_interval: Optional[int] = None
    ) -> None:
        """Start automatic backup for a conversation"""
        if conversation_id in self._backup_tasks:
            logger.warning(f"Auto backup already running for conversation {conversation_id}")
            return
        
        interval = backup_interval or self.auto_backup_interval
        
        async def backup_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    # Note: This would require integration with state manager to get current state
                    logger.debug(f"Auto backup triggered for conversation {conversation_id}")
                except asyncio.CancelledError:
                    logger.info(f"Auto backup cancelled for conversation {conversation_id}")
                    break
                except Exception as e:
                    logger.error(f"Auto backup error for conversation {conversation_id}: {e}")
        
        self._backup_tasks[conversation_id] = asyncio.create_task(backup_loop())
        logger.info(f"Started auto backup for conversation {conversation_id} with {interval}s interval")
    
    async def stop_auto_backup(self, conversation_id: str) -> None:
        """Stop automatic backup for a conversation"""
        if conversation_id in self._backup_tasks:
            self._backup_tasks[conversation_id].cancel()
            try:
                await self._backup_tasks[conversation_id]
            except asyncio.CancelledError:
                pass
            del self._backup_tasks[conversation_id]
            logger.info(f"Stopped auto backup for conversation {conversation_id}")
    
    async def cleanup_resources(self) -> None:
        """Clean up all auto backup tasks"""
        for conversation_id in list(self._backup_tasks.keys()):
            await self.stop_auto_backup(conversation_id)


class StateRecoveryFactory:
    """Factory for creating state recovery components"""
    
    @staticmethod
    def create_redis_backup_strategy(
        redis_client: redis.Redis,
        backup_key_prefix: str = "backup:",
        version_key_prefix: str = "version:",
        max_versions_per_conversation: int = 50,
        default_ttl_days: int = 30
    ) -> RedisStateBackupStrategy:
        """Create Redis-based backup strategy"""
        return RedisStateBackupStrategy(
            redis_client=redis_client,
            backup_key_prefix=backup_key_prefix,
            version_key_prefix=version_key_prefix,
            max_versions_per_conversation=max_versions_per_conversation,
            default_ttl_days=default_ttl_days
        )
    
    @staticmethod
    def create_basic_corruption_detector() -> BasicStateCorruptionDetector:
        """Create basic corruption detector"""
        return BasicStateCorruptionDetector()
    
    @staticmethod
    def create_recovery_manager(
        redis_client: redis.Redis,
        auto_backup_interval: int = 300,
        max_recovery_attempts: int = 3
    ) -> StateRecoveryManager:
        """Create complete state recovery manager"""
        backup_strategy = StateRecoveryFactory.create_redis_backup_strategy(redis_client)
        corruption_detector = StateRecoveryFactory.create_basic_corruption_detector()
        
        return StateRecoveryManager(
            backup_strategy=backup_strategy,
            corruption_detector=corruption_detector,
            auto_backup_interval=auto_backup_interval,
            max_recovery_attempts=max_recovery_attempts
        )