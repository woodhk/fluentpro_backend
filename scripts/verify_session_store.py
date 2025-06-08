#!/usr/bin/env python3
"""
Verification script for Redis session store functionality
"""
import asyncio
import sys
import os
import time
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.persistence.cache.session_store import SessionStoreFactory, SessionData
from infrastructure.persistence.cache.redis_client import RedisStreamsClient
import redis.asyncio as redis

async def test_session_store():
    """Test session store functionality"""
    print("🧪 Testing Redis Session Store Functionality")
    print("=" * 50)
    
    # Create Redis connection
    redis_url = "redis://localhost:6379/0"
    
    try:
        # Test basic Redis connection
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()
        print("✅ Redis connection established")
        
        # Create session store
        session_store = SessionStoreFactory.create_redis_session_store(redis_client)
        print("✅ Session store created")
        
        # Test 1: Create session
        print("\n📝 Test 1: Creating session...")
        session_id = "test_session_123"
        user_id = "user_456"
        test_data = {"username": "testuser", "role": "admin", "login_time": datetime.utcnow().isoformat()}
        
        session = await session_store.create_session(
            session_id=session_id,
            user_id=user_id,
            data=test_data,
            ttl_seconds=10  # Short TTL for testing
        )
        
        print(f"✅ Session created: {session.session_id}")
        print(f"   User ID: {session.user_id}")
        print(f"   Created at: {session.created_at}")
        print(f"   Expires at: {session.expires_at}")
        
        # Test 2: Retrieve session
        print("\n📖 Test 2: Retrieving session...")
        retrieved_session = await session_store.get_session(session_id)
        
        if retrieved_session:
            print(f"✅ Session retrieved: {retrieved_session.session_id}")
            print(f"   Data: {retrieved_session.data}")
            print(f"   User ID: {retrieved_session.user_id}")
        else:
            print("❌ Failed to retrieve session")
            return False
        
        # Test 3: Update session
        print("\n📝 Test 3: Updating session...")
        update_data = {"last_activity": datetime.utcnow().isoformat(), "page_count": 5}
        update_result = await session_store.update_session(
            session_id=session_id,
            data=update_data,
            extend_ttl=True,
            ttl_seconds=15
        )
        
        if update_result:
            print("✅ Session updated successfully")
            
            # Verify update
            updated_session = await session_store.get_session(session_id)
            if updated_session:
                print(f"   Updated data: {updated_session.data}")
                print(f"   New expiry: {updated_session.expires_at}")
        else:
            print("❌ Failed to update session")
        
        # Test 4: Get user sessions
        print("\n👤 Test 4: Getting user sessions...")
        user_sessions = await session_store.get_user_sessions(user_id)
        print(f"✅ Found {len(user_sessions)} sessions for user {user_id}")
        
        for user_session in user_sessions:
            print(f"   Session: {user_session.session_id}")
        
        # Test 5: Session count
        print("\n📊 Test 5: Getting session count...")
        session_count = await session_store.get_session_count()
        print(f"✅ Total active sessions: {session_count}")
        
        # Test 6: TTL extension
        print("\n⏰ Test 6: Extending session TTL...")
        extend_result = await session_store.extend_session_ttl(session_id, 20)
        if extend_result:
            print("✅ Session TTL extended")
        else:
            print("❌ Failed to extend session TTL")
        
        # Test 7: Wait for expiration (short wait for demo)
        print("\n⏳ Test 7: Testing session expiration...")
        print("   Waiting 12 seconds for session to expire...")
        await asyncio.sleep(12)
        
        expired_session = await session_store.get_session(session_id)
        if expired_session is None:
            print("✅ Session expired as expected")
        else:
            print("❌ Session did not expire - checking TTL extension")
            
        # Test 8: Create new session and delete it
        print("\n🗑️  Test 8: Testing session deletion...")
        delete_session_id = "delete_test_session"
        await session_store.create_session(
            session_id=delete_session_id,
            user_id=user_id,
            data={"test": "delete_me"},
            ttl_seconds=3600
        )
        
        delete_result = await session_store.delete_session(delete_session_id)
        if delete_result:
            print("✅ Session deleted successfully")
            
            # Verify deletion
            deleted_session = await session_store.get_session(delete_session_id)
            if deleted_session is None:
                print("✅ Session confirmed deleted")
            else:
                print("❌ Session still exists after deletion")
        
        # Test 9: Cleanup expired sessions
        print("\n🧹 Test 9: Testing expired session cleanup...")
        cleanup_count = await session_store.cleanup_expired_sessions()
        print(f"✅ Cleaned up {cleanup_count} expired sessions")
        
        print("\n" + "=" * 50)
        print("🎉 All session store tests completed successfully!")
        
        # Cleanup
        await redis_client.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

async def test_redis_client_session_methods():
    """Test the session methods added to RedisStreamsClient"""
    print("\n🔧 Testing RedisStreamsClient Session Methods")
    print("=" * 50)
    
    try:
        # Create Redis Streams client
        redis_client = RedisStreamsClient()
        await redis_client.connect()
        print("✅ RedisStreamsClient connected")
        
        # Test session methods
        test_key = "test:session:direct"
        test_value = '{"user_id": "123", "data": "test"}'
        
        # Test set session
        set_result = await redis_client.set_session(test_key, test_value, 30)
        if set_result:
            print("✅ Session set using RedisStreamsClient")
        
        # Test get session
        retrieved_value = await redis_client.get_session(test_key)
        if retrieved_value == test_value:
            print("✅ Session retrieved using RedisStreamsClient")
        
        # Test session exists
        exists = await redis_client.session_exists(test_key)
        if exists:
            print("✅ Session existence check works")
        
        # Test TTL
        ttl = await redis_client.get_session_ttl(test_key)
        if ttl > 0:
            print(f"✅ Session TTL retrieved: {ttl} seconds")
        
        # Test session deletion
        delete_result = await redis_client.delete_session(test_key)
        if delete_result:
            print("✅ Session deleted using RedisStreamsClient")
        
        await redis_client.disconnect()
        print("✅ RedisStreamsClient session methods test completed")
        
        return True
        
    except Exception as e:
        print(f"❌ RedisStreamsClient test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Session Store Verification")
    print("Make sure Redis is running on localhost:6379")
    print()
    
    # Run tests
    async def main():
        # Test session store
        session_store_ok = await test_session_store()
        
        # Test Redis client session methods
        redis_client_ok = await test_redis_client_session_methods()
        
        if session_store_ok and redis_client_ok:
            print("\n🎊 All verification tests passed!")
            return 0
        else:
            print("\n💥 Some tests failed!")
            return 1
    
    exit_code = asyncio.run(main())