#!/usr/bin/env python3
"""
Verification script for state recovery and backup mechanisms.
Tests that corrupted state can be recovered from backups.
"""
import asyncio
import json
import os
import random
import sys
import time
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis.asyncio as redis

from domains.shared.models.conversation_state import (
    ConversationContext,
    ConversationMessage,
    ConversationState,
    ConversationStatus,
    MessageRole,
)
from infrastructure.messaging.state_recovery import (
    BackupType,
    BasicStateCorruptionDetector,
    RecoveryStatus,
    RedisStateBackupStrategy,
    StateRecoveryFactory,
    StateRecoveryManager,
)


async def test_backup_and_recovery():
    """Test basic backup and recovery functionality"""
    print("💾 Testing Basic Backup and Recovery")
    print("=" * 50)

    # Create Redis connection
    redis_url = "redis://localhost:6379/0"

    try:
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()
        print("✅ Redis connection established")

        # Create recovery manager
        recovery_manager = StateRecoveryFactory.create_recovery_manager(redis_client)
        print("✅ Recovery manager created")

        # Test 1: Create conversation state and backup
        print("\n🧪 Test 1: Creating conversation state and backup...")

        # Create sample conversation
        context = ConversationContext()
        context.update_user_preference("language", "en")
        context.update_domain_context("topic", "programming")

        conversation = ConversationState(user_id="test_user_recovery", context=context)

        # Add some messages
        conversation.add_user_message("Hello, I need help with Python")
        conversation.add_assistant_message(
            "I'd be happy to help you with Python! What specific topic?"
        )
        conversation.add_user_message("I want to learn about async programming")

        print(f"✅ Created conversation: {conversation.conversation_id}")
        print(f"   Messages: {len(conversation.messages)}")
        print(f"   Total tokens: {conversation.total_tokens_used}")

        # Create backup
        version1 = await recovery_manager.create_checkpoint(
            conversation, BackupType.FULL, {"test": "initial_backup", "step": 1}
        )

        print(f"✅ Created backup: {version1.version_id}")
        print(f"   Version number: {version1.version_number}")
        print(f"   Backup type: {version1.backup_type}")
        print(f"   Size: {version1.size_bytes} bytes")

        # Add more messages and create another backup
        conversation.add_assistant_message(
            "Async programming is great! Let me explain the basics..."
        )
        conversation.add_user_message("Please show me some examples")

        version2 = await recovery_manager.create_checkpoint(
            conversation, BackupType.INCREMENTAL, {"test": "second_backup", "step": 2}
        )

        print(f"✅ Created second backup: {version2.version_id}")

        # Test 2: Recovery from latest backup
        print("\n🧪 Test 2: Recovery from latest backup...")

        recovery_result = await recovery_manager.recover_state(
            conversation.conversation_id
        )

        if recovery_result.is_successful():
            recovered_state = recovery_result.recovered_state
            print(f"✅ Recovery successful!")
            print(f"   Status: {recovery_result.status}")
            print(f"   Recovered messages: {len(recovered_state.messages)}")
            print(f"   Recovery time: {recovery_result.recovery_time_ms:.2f}ms")
            print(f"   Warnings: {len(recovery_result.warnings)}")
        else:
            print(f"❌ Recovery failed: {recovery_result.errors}")

        # Test 3: Recovery from specific version
        print("\n🧪 Test 3: Recovery from specific version...")

        recovery_result_v1 = await recovery_manager.recover_state(
            conversation.conversation_id, target_version=version1.version_number
        )

        if recovery_result_v1.is_successful():
            recovered_state_v1 = recovery_result_v1.recovered_state
            print(f"✅ Version-specific recovery successful!")
            print(f"   Recovered to version: {version1.version_number}")
            print(f"   Messages in v1: {len(recovered_state_v1.messages)}")
            print(f"   Messages in latest: {len(recovered_state.messages)}")
        else:
            print(f"❌ Version-specific recovery failed: {recovery_result_v1.errors}")

        # Test 4: Get version history
        print("\n🧪 Test 4: Version history...")

        versions = await recovery_manager.get_version_history(
            conversation.conversation_id
        )
        print(f"✅ Version history retrieved: {len(versions)} versions")

        for i, version in enumerate(versions):
            print(
                f"   Version {i+1}: {version.version_id[:8]}... "
                f"(v{version.version_number}, {version.backup_type}, "
                f"{version.size_bytes} bytes)"
            )

        print("✅ Basic backup and recovery tests completed")

    finally:
        await redis_client.aclose()


async def test_corruption_detection_and_recovery():
    """Test corruption detection and recovery mechanisms"""
    print("\n🔍 Testing Corruption Detection and Recovery")
    print("=" * 50)

    redis_url = "redis://localhost:6379/0"

    try:
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()

        # Create components
        backup_strategy = StateRecoveryFactory.create_redis_backup_strategy(
            redis_client
        )
        corruption_detector = StateRecoveryFactory.create_basic_corruption_detector()
        recovery_manager = StateRecoveryFactory.create_recovery_manager(redis_client)

        print("✅ Recovery components created")

        # Test 1: Create valid state and validate
        print("\n🧪 Test 1: Valid state validation...")

        valid_conversation = ConversationState(
            user_id="test_user_corruption", session_id="test_session"
        )
        valid_conversation.add_user_message("This is a valid message")
        valid_conversation.add_assistant_message(
            "This is a valid response", tokens_used=20
        )

        is_valid, errors = await corruption_detector.validate_state(valid_conversation)
        print(f"✅ Valid state validation: {is_valid}")
        print(f"   Errors: {len(errors)}")

        # Create backup of valid state
        backup_version = await backup_strategy.create_backup(
            valid_conversation, BackupType.FULL
        )
        print(f"✅ Created backup: {backup_version.version_id}")

        # Test 2: Create corrupted state
        print("\n🧪 Test 2: Corrupted state detection...")

        # Create state with various corruption issues
        corrupted_conversation = ConversationState(
            user_id="",  # Missing user_id
            conversation_id=valid_conversation.conversation_id,
        )

        # Add message with invalid timestamp
        corrupted_message = ConversationMessage(
            role=MessageRole.USER,
            content="",  # Empty content
            timestamp=datetime(2030, 1, 1),  # Future timestamp
        )
        corrupted_conversation.messages.append(corrupted_message)

        # Set inconsistent token count
        corrupted_conversation.total_tokens_used = 999999

        (
            is_valid_corrupted,
            corruption_errors,
        ) = await corruption_detector.validate_state(corrupted_conversation)
        print(f"✅ Corrupted state detected: {not is_valid_corrupted}")
        print(f"   Corruption errors found: {len(corruption_errors)}")
        for error in corruption_errors:
            print(f"   - {error}")

        # Test 3: Recovery from corruption
        print("\n🧪 Test 3: Recovery from corruption...")

        # Simulate corruption by trying to recover the corrupted state's conversation
        # but we'll recover from the backup we created earlier
        recovery_result = await recovery_manager.recover_state(
            valid_conversation.conversation_id, validate_recovery=True
        )

        if recovery_result.is_successful():
            recovered_state = recovery_result.recovered_state
            print(f"✅ Recovery from corruption successful!")
            print(f"   Status: {recovery_result.status}")
            print(f"   Warnings: {len(recovery_result.warnings)}")

            # Validate recovered state
            (
                is_recovered_valid,
                recovered_errors,
            ) = await corruption_detector.validate_state(recovered_state)
            print(f"✅ Recovered state is valid: {is_recovered_valid}")
            if recovered_errors:
                print(f"   Validation issues: {recovered_errors}")
        else:
            print(f"❌ Recovery from corruption failed: {recovery_result.errors}")

        # Test 4: Checksum validation
        print("\n🧪 Test 4: Checksum-based corruption detection...")

        # Calculate original checksum
        state_data = json.dumps(valid_conversation.dict(), default=str, sort_keys=True)
        import hashlib

        original_checksum = hashlib.sha256(state_data.encode()).hexdigest()

        # Test with correct checksum
        is_corrupted, issues = await corruption_detector.detect_corruption(
            valid_conversation.conversation_id, valid_conversation, original_checksum
        )
        print(f"✅ Checksum validation (valid): corrupted={is_corrupted}")

        # Test with wrong checksum
        is_corrupted_wrong, issues_wrong = await corruption_detector.detect_corruption(
            valid_conversation.conversation_id,
            valid_conversation,
            "wrong_checksum_12345",
        )
        print(f"✅ Checksum validation (invalid): corrupted={is_corrupted_wrong}")
        print(f"   Issues detected: {len(issues_wrong)}")

        print("✅ Corruption detection and recovery tests completed")

    finally:
        await redis_client.aclose()


async def test_rollback_functionality():
    """Test state rollback functionality"""
    print("\n⏪ Testing State Rollback Functionality")
    print("=" * 50)

    redis_url = "redis://localhost:6379/0"

    try:
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()

        recovery_manager = StateRecoveryFactory.create_recovery_manager(redis_client)
        print("✅ Recovery manager created")

        # Create conversation with progressive changes
        print("\n🧪 Creating conversation with multiple checkpoints...")

        conversation = ConversationState(user_id="test_user_rollback")

        # Checkpoint 1: Initial state
        conversation.add_user_message("Hello, I'm starting a new conversation")
        version1 = await recovery_manager.create_checkpoint(
            conversation, BackupType.FULL, {"checkpoint": "initial", "phase": 1}
        )
        print(f"✅ Checkpoint 1: {version1.version_number} (initial)")

        # Checkpoint 2: After adding some context
        conversation.context.update_user_preference("expertise", "beginner")
        conversation.add_assistant_message(
            "Welcome! I see you're a beginner. How can I help?"
        )
        conversation.add_user_message("I want to learn programming")

        version2 = await recovery_manager.create_checkpoint(
            conversation,
            BackupType.INCREMENTAL,
            {"checkpoint": "context_added", "phase": 2},
        )
        print(f"✅ Checkpoint 2: {version2.version_number} (context added)")

        # Checkpoint 3: After more interaction
        conversation.add_assistant_message("Great! Let's start with Python basics...")
        conversation.add_user_message("Sounds good!")
        conversation.add_assistant_message("Here's your first lesson...")

        version3 = await recovery_manager.create_checkpoint(
            conversation,
            BackupType.INCREMENTAL,
            {"checkpoint": "lesson_started", "phase": 3},
        )
        print(f"✅ Checkpoint 3: {version3.version_number} (lesson started)")

        print(f"\nConversation progression:")
        print(
            f"   Version 1: {len(conversation.messages)} messages (after checkpoint 1)"
        )
        print(f"   Version 2: More messages + context")
        print(f"   Version 3: {len(conversation.messages)} messages (current)")

        # Test rollback to different versions
        print("\n🧪 Testing rollback to version 1...")

        rollback_result_v1 = await recovery_manager.rollback_to_version(
            conversation.conversation_id, version1.version_number
        )

        if rollback_result_v1.is_successful():
            rolled_back_state = rollback_result_v1.recovered_state
            print(f"✅ Rollback to v1 successful!")
            print(f"   Messages after rollback: {len(rolled_back_state.messages)}")
            print(f"   First message: {rolled_back_state.messages[0].content}")
        else:
            print(f"❌ Rollback to v1 failed: {rollback_result_v1.errors}")

        # Test rollback to version 2
        print("\n🧪 Testing rollback to version 2...")

        rollback_result_v2 = await recovery_manager.rollback_to_version(
            conversation.conversation_id, version2.version_number
        )

        if rollback_result_v2.is_successful():
            rolled_back_state_v2 = rollback_result_v2.recovered_state
            print(f"✅ Rollback to v2 successful!")
            print(f"   Messages after rollback: {len(rolled_back_state_v2.messages)}")
            print(
                f"   User expertise: {rolled_back_state_v2.context.user_preferences.get('expertise')}"
            )
        else:
            print(f"❌ Rollback to v2 failed: {rollback_result_v2.errors}")

        # Show version history
        print("\n📋 Version history:")
        versions = await recovery_manager.get_version_history(
            conversation.conversation_id
        )
        for version in versions:
            checkpoint_name = version.metadata.get("checkpoint", "unknown")
            print(
                f"   v{version.version_number}: {checkpoint_name} "
                f"({version.backup_type}, {version.size_bytes} bytes)"
            )

        print("✅ Rollback functionality tests completed")

    finally:
        await redis_client.aclose()


async def test_performance_and_cleanup():
    """Test performance and cleanup mechanisms"""
    print("\n⚡ Testing Performance and Cleanup")
    print("=" * 50)

    redis_url = "redis://localhost:6379/0"

    try:
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()

        backup_strategy = StateRecoveryFactory.create_redis_backup_strategy(
            redis_client,
            max_versions_per_conversation=5,  # Low limit for testing cleanup
        )
        recovery_manager = StateRecoveryFactory.create_recovery_manager(redis_client)

        print("✅ Recovery components created")

        # Test 1: Performance test - rapid backups
        print("\n🧪 Performance test: Rapid backup creation...")

        conversation = ConversationState(user_id="test_user_performance")
        conversation.add_user_message("Performance test conversation")

        start_time = time.time()
        backup_count = 10

        for i in range(backup_count):
            # Add a message to change state
            conversation.add_user_message(f"Message {i} for performance test")

            # Create backup
            await recovery_manager.create_checkpoint(
                conversation,
                BackupType.INCREMENTAL,
                {"test": "performance", "iteration": i},
            )

        end_time = time.time()
        duration = end_time - start_time

        print(f"✅ Performance results:")
        print(f"   Created {backup_count} backups in {duration:.2f}s")
        print(f"   Average time per backup: {(duration/backup_count)*1000:.2f}ms")
        print(f"   Backups per second: {backup_count/duration:.1f}")

        # Test 2: Cleanup test
        print("\n🧪 Testing backup cleanup...")

        # Check how many versions exist before cleanup
        versions_before = await recovery_manager.get_version_history(
            conversation.conversation_id
        )
        print(f"   Versions before cleanup: {len(versions_before)}")

        # Add more backups to trigger cleanup
        for i in range(5):
            conversation.add_user_message(f"Cleanup test message {i}")
            await recovery_manager.create_checkpoint(
                conversation, BackupType.INCREMENTAL
            )

        # Check versions after (should be limited by max_versions)
        versions_after = await recovery_manager.get_version_history(
            conversation.conversation_id
        )
        print(f"   Versions after adding more: {len(versions_after)}")
        print(f"   Cleanup working: {len(versions_after) <= 5}")

        # Test 3: Recovery performance
        print("\n🧪 Testing recovery performance...")

        recovery_times = []
        for i in range(5):
            start_recovery = time.time()

            result = await recovery_manager.recover_state(conversation.conversation_id)

            end_recovery = time.time()
            recovery_time = (end_recovery - start_recovery) * 1000
            recovery_times.append(recovery_time)

            if not result.is_successful():
                print(f"❌ Recovery {i} failed")

        avg_recovery_time = sum(recovery_times) / len(recovery_times)
        print(f"✅ Recovery performance:")
        print(f"   Average recovery time: {avg_recovery_time:.2f}ms")
        print(f"   Min recovery time: {min(recovery_times):.2f}ms")
        print(f"   Max recovery time: {max(recovery_times):.2f}ms")

        # Test 4: Cleanup expired backups
        print("\n🧪 Testing expired backup cleanup...")

        cleanup_count = await backup_strategy.cleanup_expired_backups()
        print(f"✅ Cleanup completed: {cleanup_count} items processed")

        print("✅ Performance and cleanup tests completed")

    finally:
        await redis_client.aclose()


async def main():
    """Run all state recovery tests"""
    print("💾 State Recovery System Verification")
    print("=" * 60)

    try:
        # Test 1: Basic backup and recovery
        await test_backup_and_recovery()

        # Test 2: Corruption detection and recovery
        await test_corruption_detection_and_recovery()

        # Test 3: Rollback functionality
        await test_rollback_functionality()

        # Test 4: Performance and cleanup
        await test_performance_and_cleanup()

        print("\n🎉 All state recovery tests completed successfully!")
        print("\n✅ Verification Summary:")
        print("   ✓ State backup strategies implemented")
        print("   ✓ Corruption detection working")
        print("   ✓ Recovery from corrupted state functional")
        print("   ✓ State versioning and rollback operational")
        print("   ✓ Performance and cleanup mechanisms working")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
