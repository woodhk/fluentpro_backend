#!/usr/bin/env python3
"""
Test script for Phase 2 onboarding conversation flow
This script demonstrates the conversation flow using Amy Lu's data
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append('/Users/alex/Desktop/fluentpro_backend')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

from authentication.services.conversation_service import ConversationFlowService


def test_conversation_flow():
    """
    Test the conversation flow with Amy Lu's data
    """
    # Amy Lu's data from Supabase
    user_name = "Amy Lu"
    role = "Digital Marketing Analytics Specialist"
    industry = "Banking & Finance"
    native_language = "chinese_traditional"
    
    print("=" * 60)
    print("Phase 2 Onboarding Conversation Flow Test")
    print("=" * 60)
    print(f"User: {user_name}")
    print(f"Role: {role}")
    print(f"Industry: {industry}")
    print(f"Native Language: {native_language}")
    print("=" * 60)
    
    # Initialize conversation service
    conversation_service = ConversationFlowService()
    
    # Start conversation
    print("\n🤖 Starting conversation...")
    result = conversation_service.start_conversation(
        user_name=user_name,
        role=role,
        industry=industry,
        native_language=native_language
    )
    
    if not result.get('success'):
        print(f"❌ Failed to start conversation: {result.get('error')}")
        return
    
    print(f"✅ Conversation started successfully!")
    print(f"\n🤖 AI: {result.get('ai_response')}")
    
    conversation_state = result.get('conversation_state')
    
    # Simulate user responses for testing
    test_responses = [
        "Hello! My day is going well, thank you for asking.",
        "Yes, I'm ready to begin. Let's do this!",
        "I typically speak English with clients, colleagues, and senior management at our bank.",
        "With clients, I mainly speak English during client meetings, presentations, and consultations. For colleagues, it's mostly team meetings and project discussions.",
        "With senior management, I speak English during quarterly reviews, strategy presentations, and when reporting on analytics results."
    ]
    
    for i, user_response in enumerate(test_responses, 1):
        print(f"\n👤 User Response {i}: {user_response}")
        
        # Process the user message
        result = conversation_service.process_message(
            user_message=user_response,
            user_name=user_name,
            role=role,
            industry=industry,
            native_language=native_language,
            conversation_state=conversation_state
        )
        
        if not result.get('success'):
            print(f"❌ Failed to process message: {result.get('error')}")
            break
        
        ai_response = result.get('ai_response')
        conversation_state = result.get('conversation_state')
        is_finished = result.get('is_finished', False)
        current_step = result.get('current_step', 1)
        
        print(f"🤖 AI Response: {ai_response}")
        print(f"📊 Current Step: {current_step}")
        
        if is_finished:
            print("\n🎉 Conversation finished!")
            print("\n📋 Final Summary:")
            print(f"Communication Partners: {conversation_state.get('communication_partners', [])}")
            print(f"Work Situations: {conversation_state.get('work_situations', {})}")
            break
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("Test completed!")


if __name__ == "__main__":
    try:
        test_conversation_flow()
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()