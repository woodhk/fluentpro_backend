#!/usr/bin/env python3
"""
Test script for robust partner tracking in Phase 2 onboarding
This tests the evaluator LLM and partner completion logic
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


def test_partner_tracking():
    """
    Test that all communication partners are properly tracked and covered
    """
    # Amy Lu's data from Supabase (using English for testing)
    user_name = "Amy Lu"
    role = "Digital Marketing Analytics Specialist"
    industry = "Banking & Finance"
    native_language = "english"
    
    print("=" * 70)
    print("Testing Robust Partner Tracking System")
    print("=" * 70)
    print(f"User: {user_name}")
    print(f"Role: {role}")
    print(f"Industry: {industry}")
    print(f"Native Language: {native_language}")
    print("=" * 70)
    
    # Initialize conversation service
    conversation_service = ConversationFlowService()
    
    # Test responses that mention multiple partners
    test_conversation = [
        ("Hello", "greeting response"),
        ("Hi! My day is going great, thanks!", "day response"),
        ("Yes, I'm ready to begin!", "ready response"),
        ("I typically speak English with clients, senior management, and stakeholders at work.", "partners response"),
        ("With clients, I speak English during meetings and presentations.", "client situations"),
        ("Yes, I also do phone calls and consultations with clients.", "client completeness"),
        ("With senior management, I speak English during quarterly reviews and strategy meetings.", "management situations"),
        ("No, that covers all situations with senior management.", "management completeness"),
        ("With stakeholders, I speak English during project updates and investor presentations.", "stakeholder situations"),
        ("Yes, I also handle stakeholder calls and negotiations.", "stakeholder completeness")
    ]
    
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
    
    print(f"✅ Conversation started!")
    conversation_state = result.get('conversation_state')
    
    # Process each test message
    for i, (user_message, description) in enumerate(test_conversation[1:], 1):
        print(f"\n{'='*50}")
        print(f"Step {i}: {description}")
        print(f"👤 User: {user_message}")
        
        # Process the message
        result = conversation_service.process_message(
            user_message=user_message,
            user_name=user_name,
            role=role,
            industry=industry,
            native_language=native_language,
            conversation_state=conversation_state
        )
        
        if not result.get('success'):
            print(f"❌ Failed to process message: {result.get('error')}")
            break
        
        # Update state
        conversation_state = result.get('conversation_state')
        ai_response = result.get('ai_response')
        is_finished = result.get('is_finished', False)
        current_step = result.get('current_step', 1)
        
        # Show state information
        print(f"🤖 AI Response: {ai_response[:100]}...")
        print(f"📊 Current Step: {current_step}")
        
        # Show tracking information
        all_partners = conversation_state.get('all_partners_mentioned', [])
        partners_covered = conversation_state.get('partners_covered', [])
        current_partner = conversation_state.get('current_partner_being_asked')
        work_situations = conversation_state.get('work_situations', {})
        
        print(f"🎯 All Partners Mentioned: {all_partners}")
        print(f"✅ Partners Covered: {partners_covered}")
        print(f"🔍 Current Partner Being Asked: {current_partner}")
        print(f"📝 Work Situations Collected: {work_situations}")
        
        if is_finished:
            print("\n🎉 Conversation finished!")
            break
        
        # After step 3, test the evaluator
        if current_step == 4 and all_partners:
            print("\n🔬 Testing Evaluator LLM...")
            evaluation = conversation_service.evaluate_conversation_completeness(conversation_state)
            print(f"📊 Evaluation Result: {evaluation}")
    
    # Final verification
    print("\n" + "="*70)
    print("FINAL VERIFICATION")
    print("="*70)
    
    final_partners = conversation_state.get('all_partners_mentioned', [])
    final_covered = conversation_state.get('partners_covered', [])
    final_situations = conversation_state.get('work_situations', {})
    
    print(f"✅ Total Partners Mentioned: {len(final_partners)} - {final_partners}")
    print(f"✅ Total Partners Covered: {len(final_covered)} - {final_covered}")
    print(f"✅ All Partners Covered: {set(final_partners) == set(final_covered)}")
    
    for partner, situations in final_situations.items():
        print(f"📝 {partner}: {situations}")
    
    # Success check
    if set(final_partners) == set(final_covered) and len(final_partners) >= 3:
        print("\n🎉 SUCCESS: All partners were properly tracked and covered!")
        return True
    else:
        print("\n❌ FAILURE: Not all partners were covered properly!")
        return False


if __name__ == "__main__":
    try:
        success = test_partner_tracking()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)