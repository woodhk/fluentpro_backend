#!/usr/bin/env python3
"""
Test the fixed partner tracking system
"""

import os
import sys
import django
from django.conf import settings

sys.path.append('/Users/alex/Desktop/fluentpro_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

from authentication.services.conversation_service import ConversationFlowService


def test_fixed_tracking():
    user_name = "Amy Lu"
    role = "Digital Marketing Analytics Specialist"
    industry = "Banking & Finance"
    native_language = "english"
    
    print("=" * 60)
    print("Testing FIXED Partner Tracking System")
    print("=" * 60)
    
    conversation_service = ConversationFlowService()
    
    # Simulated conversation that should work correctly
    test_flow = [
        ("Hello", "greeting"),
        ("good", "day response"),
        ("yep", "ready response"),
        ("clients, senior management and stakeholders", "partners"),
        ("meetings, presentations", "client situations 1"),
        ("negotiations as well", "client situations 2 - should stay with clients!"),
        ("no", "client completion"),
        ("interviews, presentations and meetings", "senior mgmt situations"),
        ("no", "senior mgmt completion"),
        ("board meetings, investor calls", "stakeholder situations"),
        ("no", "stakeholder completion")
    ]
    
    result = conversation_service.start_conversation(user_name, role, industry, native_language)
    conversation_state = result.get('conversation_state')
    
    print("Starting conversation...")
    
    for i, (user_message, description) in enumerate(test_flow[1:], 1):
        print(f"\n{'='*40}")
        print(f"Step {i}: {description}")
        print(f"👤 User: {user_message}")
        
        result = conversation_service.process_message(
            user_message=user_message,
            user_name=user_name,
            role=role,
            industry=industry,
            native_language=native_language,
            conversation_state=conversation_state
        )
        
        if not result.get('success'):
            print(f"❌ Failed: {result.get('error')}")
            break
        
        conversation_state = result.get('conversation_state')
        is_finished = result.get('is_finished', False)
        
        print(f"✅ Response generated successfully")
        
        # Show critical state info
        all_partners = conversation_state.get('all_partners_mentioned', [])
        current_partner = conversation_state.get('current_partner_being_asked')
        partners_covered = conversation_state.get('partners_covered', [])
        work_situations = conversation_state.get('work_situations', {})
        
        print(f"🎯 All Partners: {all_partners}")
        print(f"🔍 Current Partner: {current_partner}")
        print(f"✅ Covered: {partners_covered}")
        print(f"📝 Situations: {work_situations}")
        
        if is_finished:
            print("\n🎉 CONVERSATION FINISHED!")
            final_analysis = conversation_state.get('final_analysis', {})
            print(f"📊 Final Analysis: {final_analysis}")
            break
    
    # Verify results
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    final_situations = conversation_state.get('work_situations', {})
    expected_partners = ['clients', 'senior management', 'stakeholders']
    
    print(f"Expected partners: {expected_partners}")
    print(f"Actual situations collected: {final_situations}")
    
    # Check if clients got all their situations
    client_situations = final_situations.get('clients', [])
    expected_client_situations = ['meetings', 'presentations', 'negotiations']
    
    print(f"\nClients situations:")
    print(f"  Expected: {expected_client_situations}")
    print(f"  Actual: {client_situations}")
    print(f"  ✅ Correct: {set(expected_client_situations).issubset(set(client_situations))}")
    
    # Check if all partners were covered
    all_covered = all(partner in final_situations for partner in expected_partners)
    print(f"\nAll partners covered: ✅ {all_covered}")
    
    return all_covered and set(expected_client_situations).issubset(set(client_situations))


if __name__ == "__main__":
    try:
        success = test_fixed_tracking()
        print(f"\n🎯 TEST RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()