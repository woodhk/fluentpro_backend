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
    Interactive test for the conversation flow with Amy Lu's data
    """
    # Amy Lu's data from Supabase (using English for testing)
    user_name = "Amy Lu"
    role = "Digital Marketing Analytics Specialist"
    industry = "Banking & Finance"
    native_language = "english"  # Changed to English for testing
    
    print("=" * 60)
    print("Phase 2 Onboarding Interactive Conversation Test")
    print("=" * 60)
    print(f"User: {user_name}")
    print(f"Role: {role}")
    print(f"Industry: {industry}")
    print(f"Native Language: {native_language}")
    print("=" * 60)
    print("Type 'quit' at any time to exit the conversation")
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
    
    # Interactive conversation loop
    while True:
        print("\n" + "-" * 40)
        
        # Get user input
        try:
            user_response = input("\n👤 Your response: ").strip()
        except KeyboardInterrupt:
            print("\n\n👋 Conversation interrupted by user. Goodbye!")
            break
        
        # Check for quit command
        if user_response.lower() in ['quit', 'exit', 'bye']:
            print("\n👋 Thanks for testing! Goodbye!")
            break
        
        if not user_response:
            print("⚠️  Please enter a response or type 'quit' to exit.")
            continue
        
        # Process the user message
        print("\n🤖 Processing your response...")
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
            continue
        
        ai_response = result.get('ai_response')
        conversation_state = result.get('conversation_state')
        is_finished = result.get('is_finished', False)
        current_step = result.get('current_step', 1)
        
        print(f"\n🤖 AI Response: {ai_response}")
        print(f"📊 Current Step: {current_step}")
        
        if is_finished:
            print("\n🎉 Conversation finished!")
            
            # Use final analysis if available, otherwise fallback to conversation state
            final_analysis = conversation_state.get('final_analysis', {})
            if final_analysis:
                print("\n📋 Final Summary (Analyzed by LLM):")
                print(f"Communication Partners: {final_analysis.get('communication_partners', [])}")
                print(f"Work Situations: {final_analysis.get('work_situations', {})}")
            else:
                print("\n📋 Final Summary (From State):")
                print(f"Communication Partners: {conversation_state.get('communication_partners', [])}")
                print(f"Work Situations: {conversation_state.get('work_situations', {})}")
            
            print("\n💾 Conversation History:")
            for i, msg in enumerate(conversation_state.get('conversation_history', []), 1):
                speaker = "👤 You" if msg['type'] == 'user' else "🤖 AI"
                print(f"{i}. {speaker}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
            break
    
    print("\n" + "=" * 60)
    print("Interactive test completed!")


if __name__ == "__main__":
    try:
        test_conversation_flow()
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()