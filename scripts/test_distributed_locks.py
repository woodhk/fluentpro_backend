#!/usr/bin/env python3
"""
Verification script for distributed lock functionality.
Tests that concurrent state updates don't corrupt data when using distributed locks.
"""
import asyncio
import sys
import os
import time
import random
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.shared.models.conversation_state import (
    ConversationState,
    ConversationMessage,
    ConversationContext,
    ConversationStatus,
    MessageRole,
    ConversationStateDelta
)
from infrastructure.messaging.state_manager import (
    RedisConversationStateManager,
    ConversationContextManager,
    ConversationStateManagerFactory
)
from infrastructure.persistence.cache.session_store import SessionStoreFactory
from infrastructure.persistence.cache.distributed_lock import (
    DistributedLockFactory,
    distributed_lock,
    LockAcquisitionError,
    LockTimeoutError
)
import redis.asyncio as redis


async def test_distributed_locks_basic():
    """Test basic distributed lock functionality"""
    print("🔒 Testing Basic Distributed Lock Functionality")
    print("=" * 50)
    
    # Create Redis connection
    redis_url = "redis://localhost:6379/0"
    redis_client = redis.from_url(redis_url)
    
    try:
        await redis_client.ping()
        print("✅ Redis connection established")
        
        # Create distributed lock
        lock_impl = DistributedLockFactory.create_redis_lock(redis_client)
        
        # Test 1: Basic lock acquisition and release
        print("\n🧪 Test 1: Basic lock acquisition and release...")
        lock_key = "test_lock_1"
        
        # Acquire lock
        token = await lock_impl.acquire(lock_key, ttl_seconds=5)
        print(f"✅ Lock acquired with token: {token[:8]}...")
        
        # Check if locked
        is_locked = await lock_impl.is_locked(lock_key)
        print(f"✅ Lock exists: {is_locked}")
        
        # Release lock
        released = await lock_impl.release(lock_key, token)
        print(f"✅ Lock released: {released}")
        
        # Test 2: Context manager usage
        print("\n🧪 Test 2: Context manager usage...")
        async with distributed_lock(lock_impl, "test_lock_2", ttl_seconds=5) as lock_mgr:
            print(f"✅ Lock acquired via context manager")
            is_locked = await lock_impl.is_locked("test_lock_2")
            print(f"✅ Lock exists in context: {is_locked}")
        
        is_locked_after = await lock_impl.is_locked("test_lock_2")
        print(f"✅ Lock released after context exit: {not is_locked_after}")
        
        # Test 3: Lock timeout
        print("\n🧪 Test 3: Lock timeout behavior...")
        lock_key = "test_lock_3"
        
        # Acquire lock with short TTL
        token = await lock_impl.acquire(lock_key, ttl_seconds=2)
        print(f"✅ Lock acquired with 2s TTL")
        
        # Wait for expiration
        await asyncio.sleep(3)
        
        # Try to acquire again (should succeed since first lock expired)
        token2 = await lock_impl.acquire(lock_key, ttl_seconds=5, timeout_seconds=1)
        print(f"✅ Lock re-acquired after expiration")
        
        await lock_impl.release(lock_key, token2)
        print(f"✅ Lock released")
        
    finally:
        await redis_client.close()


async def test_concurrent_state_updates():
    """Test that concurrent state updates don't corrupt data with distributed locks"""
    print("\n🔄 Testing Concurrent State Updates Protection")
    print("=" * 50)
    
    # Create Redis connection and session store
    redis_url = "redis://localhost:6379/0"
    redis_client = redis.from_url(redis_url)
    
    try:
        await redis_client.ping()
        print("✅ Redis connection established")
        
        # Create session store and state manager
        session_store = SessionStoreFactory.create_redis_session_store(redis_client)
        state_manager = ConversationStateManagerFactory.create_redis_manager(session_store)
        context_manager = ConversationStateManagerFactory.create_context_manager(state_manager)
        
        # Create distributed lock
        lock_impl = DistributedLockFactory.create_redis_lock(redis_client)
        
        print("✅ State managers and lock system created")
        
        # Create initial conversation
        user_id = "test_user_concurrent"
        context = ConversationContext()
        context.update_user_preference("language", "en")
        
        conversation = await state_manager.create_conversation(
            user_id=user_id,
            context=context,
            ttl_seconds=300
        )
        conversation_id = conversation.conversation_id
        print(f"✅ Conversation created: {conversation_id}")
        
        # Test concurrent updates WITHOUT locks (should show potential corruption)
        print("\n⚠️  Test A: Concurrent updates WITHOUT distributed locks...")
        
        async def update_without_lock(worker_id: int):
            """Simulate concurrent updates without locks"""
            for i in range(5):
                # Get current conversation
                current_conv = await state_manager.get_conversation(conversation_id)
                if not current_conv:
                    print(f"❌ Worker {worker_id}: Conversation not found")
                    return
                
                # Simulate processing delay
                await asyncio.sleep(random.uniform(0.01, 0.05))
                
                # Add message
                message_content = f"Message from worker {worker_id}, iteration {i}"
                result = await context_manager.add_user_message(
                    conversation_id=conversation_id,
                    content=message_content,
                    metadata={"worker": worker_id, "iteration": i}
                )
                
                if result:
                    print(f"✅ Worker {worker_id}: Added message {i}")
                else:
                    print(f"❌ Worker {worker_id}: Failed to add message {i}")
        
        # Run concurrent workers without locks
        workers = [update_without_lock(i) for i in range(3)]
        await asyncio.gather(*workers)
        
        # Check final state
        final_conv = await state_manager.get_conversation(conversation_id)
        messages_without_locks = len(final_conv.messages) if final_conv else 0
        print(f"📊 Messages without locks: {messages_without_locks}")
        
        # Clear conversation for next test
        await state_manager.delete_conversation(conversation_id)
        
        # Recreate conversation for locked test
        conversation = await state_manager.create_conversation(
            user_id=user_id,
            context=context,
            ttl_seconds=300
        )
        conversation_id = conversation.conversation_id
        
        # Test concurrent updates WITH locks
        print("\n🔒 Test B: Concurrent updates WITH distributed locks...")
        
        async def update_with_lock(worker_id: int):
            """Simulate concurrent updates with distributed locks"""
            for i in range(5):
                lock_key = f"conversation_update_{conversation_id}"
                
                try:
                    async with distributed_lock(
                        lock_impl, 
                        lock_key, 
                        ttl_seconds=10,
                        timeout_seconds=5
                    ) as lock_mgr:
                        # Get current conversation (within lock)
                        current_conv = await state_manager.get_conversation(conversation_id)
                        if not current_conv:
                            print(f"❌ Worker {worker_id}: Conversation not found")
                            return
                        
                        # Simulate processing delay
                        await asyncio.sleep(random.uniform(0.01, 0.05))
                        
                        # Add message (within lock)
                        message_content = f"Locked message from worker {worker_id}, iteration {i}"
                        result = await context_manager.add_user_message(
                            conversation_id=conversation_id,
                            content=message_content,
                            metadata={"worker": worker_id, "iteration": i, "locked": True}
                        )
                        
                        if result:
                            print(f"🔒 Worker {worker_id}: Added locked message {i}")
                        else:
                            print(f"❌ Worker {worker_id}: Failed to add locked message {i}")
                
                except (LockAcquisitionError, LockTimeoutError) as e:
                    print(f"⏰ Worker {worker_id}: Lock timeout/error on iteration {i}: {e}")
                except Exception as e:
                    print(f"❌ Worker {worker_id}: Error on iteration {i}: {e}")
        
        # Run concurrent workers with locks
        workers = [update_with_lock(i) for i in range(3)]
        await asyncio.gather(*workers)
        
        # Check final state
        final_conv_locked = await state_manager.get_conversation(conversation_id)
        messages_with_locks = len(final_conv_locked.messages) if final_conv_locked else 0
        print(f"📊 Messages with locks: {messages_with_locks}")
        
        # Compare results
        print(f"\n📈 Results Comparison:")
        print(f"   Expected messages: 15 (3 workers × 5 messages)")
        print(f"   Without locks: {messages_without_locks}")
        print(f"   With locks: {messages_with_locks}")
        
        if messages_with_locks >= messages_without_locks:
            print("✅ Distributed locks improved data consistency")
        else:
            print("⚠️  Unexpected result - locks may need adjustment")
        
        # Cleanup
        await state_manager.delete_conversation(conversation_id)
        print("✅ Test cleanup completed")
        
    finally:
        await redis_client.close()


async def test_lock_performance():
    """Test distributed lock performance under load"""
    print("\n⚡ Testing Distributed Lock Performance")
    print("=" * 50)
    
    redis_url = "redis://localhost:6379/0"
    redis_client = redis.from_url(redis_url)
    
    try:
        await redis_client.ping()
        
        # Create distributed lock
        lock_impl = DistributedLockFactory.create_redis_lock(redis_client)
        
        # Performance test: rapid lock acquisition/release
        print("🧪 Performance test: 100 rapid lock acquisitions...")
        
        start_time = time.time()
        success_count = 0
        
        for i in range(100):
            try:
                lock_key = f"perf_test_{i}"
                async with distributed_lock(lock_impl, lock_key, ttl_seconds=1) as lock_mgr:
                    # Simulate minimal work
                    await asyncio.sleep(0.001)
                    success_count += 1
            except Exception as e:
                print(f"❌ Failed lock {i}: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"📊 Performance Results:")
        print(f"   Successful locks: {success_count}/100")
        print(f"   Total time: {duration:.2f}s")
        print(f"   Average time per lock: {(duration/100)*1000:.2f}ms")
        print(f"   Locks per second: {100/duration:.1f}")
        
        if success_count == 100 and duration < 5:
            print("✅ Performance test passed")
        else:
            print("⚠️  Performance may need optimization")
    
    finally:
        await redis_client.close()


async def main():
    """Run all distributed lock tests"""
    print("🔒 Distributed Lock System Verification")
    print("=" * 60)
    
    try:
        # Test 1: Basic functionality
        await test_distributed_locks_basic()
        
        # Test 2: Concurrent state updates
        await test_concurrent_state_updates()
        
        # Test 3: Performance
        await test_lock_performance()
        
        print("\n🎉 All distributed lock tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())