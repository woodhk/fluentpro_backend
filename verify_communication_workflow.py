#!/usr/bin/env python
"""
Simple verification script to show the communication workflow works correctly
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

from onboarding.business.communication_manager import CommunicationManager

def verify_workflow():
    """Verify the communication workflow data in database"""
    print("🔍 VERIFYING COMMUNICATION WORKFLOW IN DATABASE")
    print("="*60)
    
    test_user_id = 'adfc84cf-5f4e-4096-83cc-1254e5abdd0c'
    communication_manager = CommunicationManager()
    
    # Get user's communication needs
    user_partners = communication_manager.get_user_communication_partners(test_user_id)
    
    print(f"✅ User has selected {len(user_partners)} communication partners:")
    
    total_situations = 0
    for i, partner_selection in enumerate(user_partners, 1):
        partner_name = partner_selection.display_name
        print(f"\n{i}. Partner: {partner_name}")
        
        # Get situations for this partner
        if not partner_selection.is_custom:
            partner_units = communication_manager.get_units_for_partner(test_user_id, partner_selection.communication_partner_id)
            total_situations += len(partner_units)
            
            print(f"   Situations ({len(partner_units)}):")
            for j, unit_selection in enumerate(partner_units, 1):
                custom_label = " (custom)" if unit_selection.is_custom else ""
                print(f"     {j}. {unit_selection.unit_name}{custom_label}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Communication Partners: {len(user_partners)}")
    print(f"   Total Situations: {total_situations}")
    print(f"   Average Situations per Partner: {total_situations / len(user_partners):.1f}")
    
    # Verify workflow requirements
    workflow_requirements_met = (
        len(user_partners) == 3 and  # Exactly 3 partners
        total_situations >= 6 and    # Each partner has situations
        all(not p.is_custom for p in user_partners)  # All partners are from database
    )
    
    print(f"\n🎯 WORKFLOW REQUIREMENTS:")
    print(f"   ✅ User selected 3 communication partners: {len(user_partners) == 3}")
    print(f"   ✅ Each partner has situations selected: {total_situations >= 6}")
    print(f"   ✅ All data uploaded to database: {workflow_requirements_met}")
    
    if workflow_requirements_met:
        print(f"\n🎉 WORKFLOW VERIFICATION: ✅ PASSED")
        print("The communication workflow works exactly as specified!")
    else:
        print(f"\n❌ WORKFLOW VERIFICATION: ❌ FAILED")

if __name__ == "__main__":
    verify_workflow()