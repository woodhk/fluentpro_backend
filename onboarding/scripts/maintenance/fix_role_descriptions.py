#!/usr/bin/env python
"""
Script to fix role descriptions that have unwanted formatting.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fluentpro_backend.settings')
django.setup()

from authentication.services.openai_service import OpenAIService
from authentication.services.supabase_service import SupabaseService

def fix_role_descriptions():
    """Fix role descriptions that have unwanted formatting."""
    print("🛠️  Fixing Role Descriptions with Bad Formatting")
    print("=" * 60)
    
    try:
        # Initialize services
        openai_service = OpenAIService()
        supabase_service = SupabaseService()
        
        # Get roles with bad formatting
        roles_data = supabase_service.get_all_roles_with_industry()
        roles_to_fix = []
        
        for role in roles_data:
            description = role.get('description', '')
            # Check if description has the formatting issues
            if ('**Job Title:' in description or 
                '**Description:**' in description or 
                description.startswith('**') or
                'Job Title:' in description and 'Description:' in description):
                roles_to_fix.append(role)
        
        print(f"📊 Found {len(roles_to_fix)} roles with formatting issues:")
        for role in roles_to_fix:
            print(f"   • {role['title']} (ID: {role['id']})")
        
        if not roles_to_fix:
            print("✅ No roles with formatting issues found!")
            return
        
        # Fix each role
        for i, role in enumerate(roles_to_fix, 1):
            print(f"\n🔧 Fixing {i}/{len(roles_to_fix)}: {role['title']}")
            
            original_description = role['description']
            print(f"   Original: {original_description[:100]}...")
            
            # Clean the description
            cleaned_description = openai_service._clean_description_formatting(original_description)
            print(f"   Cleaned: {cleaned_description[:100]}...")
            
            # Update in database
            try:
                # Use raw SQL to update the role description
                update_sql = """
                UPDATE roles 
                SET description = %s 
                WHERE id = %s
                """
                
                # Execute the update (we'll need to do this through supabase service)
                result = supabase_service.supabase.table('roles').update({
                    'description': cleaned_description
                }).eq('id', role['id']).execute()
                
                if result.data:
                    print(f"   ✅ Successfully updated role {role['title']}")
                else:
                    print(f"   ❌ Failed to update role {role['title']}")
                    
            except Exception as e:
                print(f"   ❌ Error updating role {role['title']}: {str(e)}")
                continue
        
        print(f"\n🎉 Completed fixing role descriptions!")
        
        # Verify the fixes
        print(f"\n🔍 Verifying fixes...")
        updated_roles = supabase_service.get_all_roles_with_industry()
        remaining_issues = []
        
        for role in updated_roles:
            description = role.get('description', '')
            if ('**Job Title:' in description or 
                '**Description:**' in description or 
                'Job Title:' in description and 'Description:' in description):
                remaining_issues.append(role)
        
        if remaining_issues:
            print(f"   ⚠️  {len(remaining_issues)} roles still have formatting issues:")
            for role in remaining_issues:
                print(f"      • {role['title']} (ID: {role['id']})")
        else:
            print(f"   ✅ All role descriptions are now properly formatted!")
            
    except Exception as e:
        print(f"❌ Critical error during role description fixing: {str(e)}")

if __name__ == "__main__":
    fix_role_descriptions()