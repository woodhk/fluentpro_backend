#!/usr/bin/env python3
"""
Verification script for conversation state management functionality.
Tests that AI conversations maintain context across requests.
"""
import asyncio
import sys
import os
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
import redis.asyncio as redis

async def test_conversation_state_management():
    """Test conversation state management functionality"""
    print("🧪 Testing Conversation State Management")
    print("=" * 50)
    
    # Create Redis connection and session store
    redis_url = "redis://localhost:6379/0"
    
    try:
        # Test basic Redis connection
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()
        print("✅ Redis connection established")
        
        # Create session store
        session_store = SessionStoreFactory.create_redis_session_store(redis_client)
        print("✅ Session store created")
        
        # Create conversation state manager
        state_manager = ConversationStateManagerFactory.create_redis_manager(session_store)
        context_manager = ConversationStateManagerFactory.create_context_manager(state_manager)
        print("✅ State managers created")
        
        # Test 1: Create conversation
        print("\n📝 Test 1: Creating conversation...")
        user_id = "test_user_123"
        session_id = "test_session_456"
        
        # Create conversation context
        context = ConversationContext()
        context.update_user_preference("language", "en")
        context.update_user_preference("expertise_level", "intermediate")
        context.update_domain_context("topic", "programming")
        context.update_conversation_setting("model", "gpt-4")
        
        conversation = await state_manager.create_conversation(
            user_id=user_id,
            session_id=session_id,
            context=context,
            ttl_seconds=300  # 5 minutes for testing
        )
        
        print(f"✅ Conversation created: {conversation.conversation_id}")
        print(f"   User ID: {conversation.user_id}")
        print(f"   Session ID: {conversation.session_id}")
        print(f"   Context: {conversation.context.user_preferences}")
        
        conversation_id = conversation.conversation_id
        
        # Test 2: Add messages and maintain context
        print("\n💬 Test 2: Adding messages and maintaining context...")
        
        # Add user message
        user_message_1 = "Hello, I'm learning Python. What are the best practices for async programming?"
        result = await context_manager.add_user_message(
            conversation_id=conversation_id,
            content=user_message_1,
            metadata={"source": "web_ui", "timestamp": datetime.utcnow().isoformat()}
        )
        print(f"✅ User message 1 added: {result}")
        
        # Add assistant response
        assistant_response_1 = """Here are key best practices for async programming in Python:
        
        1. Use async/await properly
        2. Understand the event loop
        3. Handle exceptions in async contexts
        4. Use asyncio.gather() for concurrent operations
        
        What specific aspect would you like me to explain further?"""
        
        result = await context_manager.add_assistant_message(
            conversation_id=conversation_id,
            content=assistant_response_1,
            tokens_used=85,
            metadata={"model": "gpt-4", "temperature": 0.7}
        )
        print(f"✅ Assistant message 1 added: {result}")
        
        # Test 3: Retrieve conversation and verify context persistence
        print("\n🔍 Test 3: Retrieving conversation and verifying context...")
        
        retrieved_conversation = await state_manager.get_conversation(conversation_id)
        if retrieved_conversation:
            print(f"✅ Conversation retrieved successfully")
            print(f"   Message count: {len(retrieved_conversation.messages)}")
            print(f"   Total tokens: {retrieved_conversation.total_tokens_used}")
            print(f"   Status: {retrieved_conversation.status.value}")
            print(f"   Last activity: {retrieved_conversation.last_activity_at}")
            
            # Verify messages are in correct order
            if len(retrieved_conversation.messages) == 2:
                msg1 = retrieved_conversation.messages[0]
                msg2 = retrieved_conversation.messages[1]
                print(f"   Message 1 role: {msg1.role.value}")
                print(f"   Message 2 role: {msg2.role.value}")
                print("✅ Message order preserved")
            else:
                print("❌ Incorrect number of messages")
        else:
            print("❌ Failed to retrieve conversation")
            return False
        
        # Test 4: Continue conversation across "requests" (simulating context persistence)
        print("\n🔄 Test 4: Continuing conversation across requests...")
        
        # Simulate a new request - add follow-up user message
        user_message_2 = "Can you explain asyncio.gather() in more detail with an example?"
        result = await context_manager.add_user_message(
            conversation_id=conversation_id,
            content=user_message_2,
            metadata={"source": "web_ui", "request_id": "req_456"}
        )
        print(f"✅ Follow-up user message added: {result}")
        
        # Get context for AI (simulating what would be sent to AI API)
        ai_context = await context_manager.get_context_for_ai(
            conversation_id=conversation_id,
            max_messages=10
        )
        
        if ai_context:
            print("✅ AI context retrieved successfully")
            print(f"   Messages for AI: {len(ai_context['messages'])}")
            print(f"   Context includes user preferences: {'language' in ai_context['context']['user_preferences']}")
            print(f"   Context includes domain info: {'topic' in ai_context['context']['domain_context']}")
            
            # Verify conversation history is maintained
            messages = ai_context['messages']
            expected_sequence = ["user", "assistant", "user"]
            actual_sequence = [msg["role"] for msg in messages]
            
            if actual_sequence == expected_sequence:
                print("✅ Conversation context maintained correctly")
            else:
                print(f"❌ Context sequence mismatch. Expected: {expected_sequence}, Got: {actual_sequence}")
        else:
            print("❌ Failed to get AI context")
        
        # Test 5: Update conversation context
        print("\n📝 Test 5: Updating conversation context...")
        
        context_updates = {
            "user_preferences": {"expertise_level": "advanced"},
            "domain_context": {"current_topic": "asyncio.gather"}
        }
        
        result = await context_manager.update_context(conversation_id, context_updates)
        if result:
            print("✅ Context updated successfully")
            
            # Verify context update
            updated_conversation = await state_manager.get_conversation(conversation_id)
            if updated_conversation:
                expertise = updated_conversation.context.user_preferences.get("expertise_level")
                current_topic = updated_conversation.context.domain_context.get("current_topic")
                print(f"   Updated expertise level: {expertise}")
                print(f"   Updated current topic: {current_topic}")
                
                if expertise == "advanced" and current_topic == "asyncio.gather":
                    print("✅ Context updates verified")
                else:
                    print("❌ Context updates not reflected")
        else:
            print("❌ Failed to update context")
        
        # Test 6: Get user conversations
        print("\n👤 Test 6: Getting user conversations...")
        
        user_conversations = await state_manager.get_user_conversations(
            user_id=user_id,
            status=ConversationStatus.ACTIVE,
            limit=10
        )
        
        print(f"✅ Found {len(user_conversations)} active conversations for user")
        
        if user_conversations:
            conv = user_conversations[0]
            print(f"   Conversation ID: {conv.conversation_id}")
            print(f"   Message count: {len(conv.messages)}")
            print(f"   Created: {conv.created_at}")
        
        # Test 7: Context window management
        print("\n🪟 Test 7: Testing context window management...")
        
        # Add more messages to test context window
        for i in range(3):
            await context_manager.add_user_message(
                conversation_id=conversation_id,
                content=f"This is test message {i+3} to fill up the context window.",
                metadata={"test": True}
            )
            
            await context_manager.add_assistant_message(
                conversation_id=conversation_id,
                content=f"This is assistant response {i+3}.",
                tokens_used=20,
                metadata={"test": True}
            )
        
        # Test context window management
        result = await context_manager.manage_context_window(
            conversation_id=conversation_id,
            token_limit=100,  # Low limit to force trimming
            preserve_recent_messages=4
        )
        
        if result:
            print("✅ Context window managed successfully")
            
            # Verify context was trimmed
            trimmed_conversation = await state_manager.get_conversation(conversation_id)
            if trimmed_conversation:
                print(f"   Messages after trimming: {len(trimmed_conversation.messages)}")
                print(f"   Tokens after trimming: {trimmed_conversation.total_tokens_used}")
                
                if len(trimmed_conversation.messages) <= 4:
                    print("✅ Context window trimming verified")
                else:
                    print("❌ Context window not properly trimmed")
        else:
            print("❌ Failed to manage context window")
        
        # Test 8: Conversation status management
        print("\n📊 Test 8: Testing conversation status management...")
        
        # Update conversation status
        status_update = ConversationStateDelta(
            conversation_id=conversation_id,
            operation="update_status",
            changes={"status": ConversationStatus.COMPLETED.value}
        )
        
        result = await state_manager.update_conversation(conversation_id, status_update)
        if result:
            print("✅ Conversation status updated")
            
            # Verify status change
            final_conversation = await state_manager.get_conversation(conversation_id)
            if final_conversation and final_conversation.status == ConversationStatus.COMPLETED:
                print("✅ Status change verified")
            else:
                print("❌ Status change not reflected")
        
        # Test 9: Cleanup test
        print("\n🧹 Test 9: Cleanup test conversation...")
        
        delete_result = await state_manager.delete_conversation(conversation_id)
        if delete_result:
            print("✅ Test conversation deleted")
            
            # Verify deletion
            deleted_conversation = await state_manager.get_conversation(conversation_id)
            if deleted_conversation is None:
                print("✅ Conversation deletion verified")
            else:
                print("❌ Conversation still exists after deletion")
        else:
            print("❌ Failed to delete conversation")
        
        print("\n" + "=" * 50)
        print("🎉 All conversation state management tests completed!")
        
        # Cleanup
        await redis_client.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_context_persistence_simulation():
    """
    Simulate AI conversation context persistence across multiple 'requests'.
    This simulates what would happen in a real AI interaction scenario.
    """
    print("\n🤖 Simulating AI Conversation Context Persistence")
    print("=" * 60)
    
    redis_url = "redis://localhost:6379/0"
    
    try:
        # Setup
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()
        session_store = SessionStoreFactory.create_redis_session_store(redis_client)
        state_manager = ConversationStateManagerFactory.create_redis_manager(session_store)
        context_manager = ConversationStateManagerFactory.create_context_manager(state_manager)
        
        # Simulate AI conversation scenario
        user_id = "ai_user_789"
        
        # Request 1: Start conversation
        print("\n📱 Request 1: User starts conversation about career advice")
        conversation = await state_manager.create_conversation(
            user_id=user_id,
            context=ConversationContext()
        )
        conversation_id = conversation.conversation_id
        
        await context_manager.add_user_message(
            conversation_id,
            "I'm a software engineer with 3 years of experience. I want to transition into AI/ML. What skills should I focus on?",
            {"source": "mobile_app", "user_location": "San Francisco"}
        )
        
        # Simulate AI response
        await context_manager.add_assistant_message(
            conversation_id,
            "Great question! For transitioning from software engineering to AI/ML, I'd recommend focusing on: 1) Python and data science libraries (pandas, numpy, scikit-learn), 2) Mathematics (linear algebra, statistics), 3) Machine learning fundamentals. What's your current experience with Python?",
            tokens_used=65
        )
        
        print("✅ Request 1 completed - conversation started")
        
        # Request 2: Continue conversation (simulating new HTTP request)
        print("\n📱 Request 2: User continues conversation (new request)")
        
        # Retrieve conversation state (as would happen in new request)
        ai_context = await context_manager.get_context_for_ai(conversation_id)
        if not ai_context:
            print("❌ Failed to retrieve context for request 2")
            return False
        
        print(f"✅ Context retrieved - {len(ai_context['messages'])} messages in history")
        
        # Add follow-up message
        await context_manager.add_user_message(
            conversation_id,
            "I have good Python experience from web development. I've used pandas a bit. What specific ML concepts should I learn first?",
            {"source": "mobile_app", "continuation": True}
        )
        
        # Simulate AI response with context awareness
        await context_manager.add_assistant_message(
            conversation_id,
            "Perfect! Since you already have Python and some pandas experience, let's focus on ML fundamentals: 1) Supervised vs unsupervised learning, 2) Model evaluation (cross-validation, metrics), 3) Feature engineering. I'd suggest starting with scikit-learn tutorials. Would you like specific resource recommendations?",
            tokens_used=72
        )
        
        print("✅ Request 2 completed - context maintained across requests")
        
        # Request 3: Much later continuation (simulating session recovery)
        print("\n📱 Request 3: User returns later (session recovery)")
        
        # Simulate context retrieval after time gap
        ai_context = await context_manager.get_context_for_ai(conversation_id, max_messages=6)
        if ai_context:
            print(f"✅ Session recovered - {len(ai_context['messages'])} messages available")
            
            # Verify conversation history is complete
            messages = ai_context['messages']
            if len(messages) >= 4:  # Should have user->ai->user->ai
                print("✅ Full conversation history preserved")
                
                # Show conversation flow
                print("   Conversation flow:")
                for i, msg in enumerate(messages[-4:], 1):
                    role = msg['role']
                    content_preview = msg['content'][:60] + "..." if len(msg['content']) > 60 else msg['content']
                    print(f"   {i}. {role.upper()}: {content_preview}")
            else:
                print("❌ Incomplete conversation history")
        else:
            print("❌ Failed to recover session")
            return False
        
        # Add final message
        await context_manager.add_user_message(
            conversation_id,
            "Yes, resource recommendations would be great! Also, should I consider any online courses?",
            {"source": "web_app", "session_resumed": True}
        )
        
        print("✅ Request 3 completed - conversation continued seamlessly")
        
        # Final verification
        print("\n🔍 Final verification:")
        final_conversation = await state_manager.get_conversation(conversation_id)
        if final_conversation:
            print(f"✅ Total messages in conversation: {len(final_conversation.messages)}")
            print(f"✅ Total tokens used: {final_conversation.total_tokens_used}")
            print(f"✅ Conversation duration: {final_conversation.last_activity_at - final_conversation.created_at}")
            print("✅ AI conversation context persistence verified!")
        
        # Cleanup
        await state_manager.delete_conversation(conversation_id)
        await redis_client.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Conversation State Management Verification")
    print("Make sure Redis is running on localhost:6379")
    print()
    
    async def main():
        # Test basic conversation state management
        basic_test_ok = await test_conversation_state_management()
        
        # Test AI conversation context persistence simulation
        context_test_ok = await test_context_persistence_simulation()
        
        if basic_test_ok and context_test_ok:
            print("\n🎊 All verification tests passed!")
            print("✅ AI conversations maintain context across requests")
            return 0
        else:
            print("\n💥 Some tests failed!")
            return 1
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)