#!/usr/bin/env python3
"""
Demonstration of state debugging and monitoring tools.
Shows functionality without requiring Redis connection.
"""
import sys
import os
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.shared.models.conversation_state import (
    ConversationState,
    ConversationContext,
    ConversationStatus,
    MessageRole
)
from infrastructure.messaging.state_recovery import StateRecoveryFactory


def demonstrate_state_visualization():
    """Demonstrate state visualization capabilities"""
    print("📊 State Visualization Demonstration")
    print("=" * 50)
    
    # Create a comprehensive conversation example
    conversation = ConversationState(
        user_id="demo_user_12345",
        session_id="demo_session_abc"
    )
    
    # Add realistic conversation flow
    conversation.add_user_message("Hi! I'm new to programming and want to learn Python.")
    conversation.add_assistant_message(
        "Welcome! That's a great choice. Python is an excellent language for beginners. "
        "What specific area interests you most - web development, data science, or automation?",
        tokens_used=35
    )
    conversation.add_user_message("I'm really interested in data science and machine learning.")
    conversation.add_assistant_message(
        "Perfect! For data science with Python, you'll want to learn libraries like pandas, "
        "numpy, matplotlib, and scikit-learn. Should we start with the basics?",
        tokens_used=42
    )
    conversation.add_user_message("Yes, let's start with pandas. How do I install it?")
    conversation.add_assistant_message(
        "You can install pandas using pip: `pip install pandas`. Once installed, "
        "you can import it with `import pandas as pd`. Would you like to see a simple example?",
        tokens_used=38
    )
    
    # Set up rich context
    conversation.context.update_user_preference("experience_level", "beginner")
    conversation.context.update_user_preference("learning_goal", "data_science")
    conversation.context.update_user_preference("preferred_language", "python")
    conversation.context.update_domain_context("topic", "programming")
    conversation.context.update_domain_context("subtopic", "data_science")
    conversation.context.update_conversation_setting("model", "gpt-4")
    conversation.context.update_conversation_setting("temperature", 0.7)
    
    # Add tags and metadata
    conversation.add_tag("learning")
    conversation.add_tag("python")
    conversation.add_tag("data_science")
    conversation.add_tag("beginner")
    conversation.metadata["source"] = "web_ui"
    conversation.metadata["onboarding_step"] = "language_selection"
    conversation.metadata["user_timezone"] = "UTC-8"
    
    # Set token limit for demonstration
    conversation.token_limit = 200
    
    print("✅ Created demonstration conversation")
    print()
    
    # Show basic information
    print("📋 Basic Information:")
    print(f"   ID: {conversation.conversation_id}")
    print(f"   User: {conversation.user_id}")
    print(f"   Session: {conversation.session_id}")
    print(f"   Status: {conversation.status.value}")
    print(f"   Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Messages: {len(conversation.messages)}")
    print(f"   Tags: {', '.join(conversation.tags)}")
    print()
    
    # Show token analysis
    print("🎯 Token Analysis:")
    print(f"   Total Tokens: {conversation.total_tokens_used}")
    print(f"   Token Limit: {conversation.token_limit}")
    usage_pct = (conversation.total_tokens_used / conversation.token_limit) * 100
    print(f"   Usage: {usage_pct:.1f}%")
    print(f"   Near Limit: {'⚠️  Yes' if conversation.is_near_token_limit() else '✅ No'}")
    print()
    
    # Show message breakdown
    print("💬 Message Analysis:")
    user_msgs = sum(1 for msg in conversation.messages if msg.role == MessageRole.USER)
    assistant_msgs = sum(1 for msg in conversation.messages if msg.role == MessageRole.ASSISTANT)
    print(f"   User Messages: {user_msgs}")
    print(f"   Assistant Messages: {assistant_msgs}")
    print(f"   Response Ratio: {assistant_msgs/user_msgs:.2f}")
    print()
    
    # Show context summary
    print("⚙️  Context Summary:")
    context_for_ai = conversation.context.get_context_for_ai()
    print(f"   User Preferences: {len(context_for_ai.get('user_preferences', {}))}")
    for key, value in context_for_ai.get('user_preferences', {}).items():
        print(f"     - {key}: {value}")
    print(f"   Domain Context: {len(context_for_ai.get('domain_context', {}))}")
    for key, value in context_for_ai.get('domain_context', {}).items():
        print(f"     - {key}: {value}")
    print()
    
    # Show conversation flow
    print("🔄 Conversation Flow:")
    for i, msg in enumerate(conversation.messages, 1):
        role_emoji = "👤" if msg.role == MessageRole.USER else "🤖"
        tokens_info = f" ({msg.tokens_used} tokens)" if msg.tokens_used else ""
        print(f"   {i}. {role_emoji} {msg.role.value.title()}{tokens_info}:")
        print(f"      {msg.content[:80]}{'...' if len(msg.content) > 80 else ''}")
    print()
    
    return conversation


def demonstrate_issue_detection(conversation):
    """Demonstrate issue detection capabilities"""
    print("🔍 Issue Detection Demonstration")
    print("=" * 50)
    
    # Create various problematic conversations
    issues_found = []
    
    # Issue 1: Token limit approaching
    if conversation.is_near_token_limit(threshold=0.6):
        issues_found.append("Token usage is approaching limit")
    
    # Issue 2: Conversation age analysis
    age_hours = (datetime.utcnow() - conversation.created_at).total_seconds() / 3600
    if age_hours > 24:
        issues_found.append(f"Long-running conversation ({age_hours:.1f} hours)")
    
    # Issue 3: Message count analysis
    if len(conversation.messages) > 100:
        issues_found.append(f"High message count ({len(conversation.messages)})")
    
    # Issue 4: Token efficiency analysis
    if conversation.total_tokens_used > 0:
        avg_tokens_per_message = conversation.total_tokens_used / len(conversation.messages)
        if avg_tokens_per_message > 100:
            issues_found.append(f"High average tokens per message ({avg_tokens_per_message:.1f})")
    
    print("✅ Issue Detection Results:")
    if issues_found:
        for issue in issues_found:
            print(f"   ⚠️  {issue}")
    else:
        print("   ✅ No issues detected")
    print()
    
    # Create additional problematic conversations for comparison
    print("🧪 Testing with Problematic Conversations:")
    
    # Large conversation
    large_conv = ConversationState(user_id="heavy_user")
    for i in range(150):
        large_conv.add_user_message(f"Message {i}")
    
    print(f"   📊 Large Conversation: {len(large_conv.messages)} messages")
    
    # Token-heavy conversation
    token_heavy = ConversationState(user_id="token_user")
    token_heavy.add_user_message("Test message")
    token_heavy.total_tokens_used = 8500
    token_heavy.token_limit = 10000
    
    print(f"   🎯 Token-Heavy: {token_heavy.total_tokens_used}/{token_heavy.token_limit} tokens")
    print(f"      Usage: {(token_heavy.total_tokens_used/token_heavy.token_limit)*100:.1f}%")
    
    # Old conversation
    old_conv = ConversationState(user_id="inactive_user")
    old_conv.created_at = datetime.utcnow() - timedelta(days=10)
    old_conv.last_activity_at = datetime.utcnow() - timedelta(days=8)
    old_conv.add_user_message("Old conversation")
    
    age_days = (datetime.utcnow() - old_conv.created_at).days
    inactive_days = (datetime.utcnow() - old_conv.last_activity_at).days
    print(f"   📅 Old Conversation: {age_days} days old, {inactive_days} days inactive")
    
    print()


async def demonstrate_validation():
    """Demonstrate state validation capabilities"""
    print("✅ State Validation Demonstration")
    print("=" * 50)
    
    # Create corruption detector
    corruption_detector = StateRecoveryFactory.create_basic_corruption_detector()
    
    # Test with valid conversation
    valid_conv = ConversationState(user_id="valid_user")
    valid_conv.add_user_message("Hello!")
    valid_conv.add_assistant_message("Hi there!", tokens_used=10)
    
    is_valid, errors = await corruption_detector.validate_state(valid_conv)
    print(f"✅ Valid Conversation Check:")
    print(f"   Valid: {'✅ Yes' if is_valid else '❌ No'}")
    if errors:
        print(f"   Errors: {len(errors)}")
        for error in errors:
            print(f"     - {error}")
    print()
    
    # Test with problematic conversations
    print("🧪 Testing Problematic States:")
    
    # Missing user ID
    invalid_conv1 = ConversationState(user_id="")  # Empty user ID
    invalid_conv1.add_user_message("Test")
    
    is_valid1, errors1 = await corruption_detector.validate_state(invalid_conv1)
    print(f"   1. Empty User ID: {'✅ Valid' if is_valid1 else '❌ Invalid'}")
    if errors1:
        for error in errors1[:2]:  # Show first 2 errors
            print(f"      - {error}")
    
    # Token mismatch
    invalid_conv2 = ConversationState(user_id="token_mismatch_user")
    invalid_conv2.add_user_message("Test", {"tokens": 50})
    invalid_conv2.total_tokens_used = 200  # Doesn't match
    
    is_valid2, errors2 = await corruption_detector.validate_state(invalid_conv2)
    print(f"   2. Token Mismatch: {'✅ Valid' if is_valid2 else '❌ Invalid'}")
    if errors2:
        for error in errors2[:2]:
            print(f"      - {error}")
    
    # Future timestamps
    invalid_conv3 = ConversationState(user_id="future_user")
    invalid_conv3.created_at = datetime.utcnow() + timedelta(days=1)  # Future date
    
    is_valid3, errors3 = await corruption_detector.validate_state(invalid_conv3)
    print(f"   3. Future Timestamp: {'✅ Valid' if is_valid3 else '❌ Invalid'}")
    if errors3:
        for error in errors3[:2]:
            print(f"      - {error}")
    
    print()


def demonstrate_cli_usage():
    """Demonstrate CLI tool usage"""
    print("🔧 CLI Tool Usage Examples")
    print("=" * 50)
    
    print("The State Inspector CLI provides powerful debugging capabilities:")
    print()
    
    print("📋 List conversations:")
    print("   python scripts/debug/state_inspector.py list")
    print("   python scripts/debug/state_inspector.py list --user-id user123 --detailed")
    print()
    
    print("🔍 Inspect specific conversation:")
    print("   python scripts/debug/state_inspector.py inspect <conversation-id>")
    print("   python scripts/debug/state_inspector.py inspect <conversation-id> --show-metadata")
    print()
    
    print("🔎 Search conversations:")
    print("   python scripts/debug/state_inspector.py search 'python' --type content")
    print("   python scripts/debug/state_inspector.py search 'user123' --type user")
    print("   python scripts/debug/state_inspector.py search 'learning' --type tags")
    print()
    
    print("🏥 Health analysis:")
    print("   python scripts/debug/state_inspector.py health <conversation-id>")
    print()
    
    print("📤 Export conversation:")
    print("   python scripts/debug/state_inspector.py export <conversation-id> output.json")
    print("   python scripts/debug/state_inspector.py export <conversation-id> output.txt --format txt")
    print()
    
    print("📊 View statistics:")
    print("   python scripts/debug/state_inspector.py stats")
    print()


def main():
    """Run complete debugging tools demonstration"""
    print("🛠️  State Debugging and Monitoring Tools Demo")
    print("=" * 60)
    print()
    
    # Demonstrate state visualization
    conversation = demonstrate_state_visualization()
    
    # Demonstrate issue detection
    demonstrate_issue_detection(conversation)
    
    # Demonstrate validation
    import asyncio
    asyncio.run(demonstrate_validation())
    
    # Demonstrate CLI usage
    demonstrate_cli_usage()
    
    print("🎉 Debugging Tools Demonstration Complete!")
    print()
    print("Key Features Demonstrated:")
    print("✓ Comprehensive state visualization")
    print("✓ Issue detection and analysis")
    print("✓ State validation and corruption detection")
    print("✓ Powerful CLI for debugging operations")
    print("✓ Health monitoring and metrics collection")
    print("✓ Search and filtering capabilities")
    print("✓ Export functionality for external analysis")


if __name__ == "__main__":
    main()