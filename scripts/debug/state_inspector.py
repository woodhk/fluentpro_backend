#!/usr/bin/env python3
"""
State Inspector - Debug tool for conversation state management.

Provides CLI utilities for inspecting, analyzing, and debugging conversation states
with visualization, search, and validation capabilities.
"""

import asyncio
import sys
import os
import json
import argparse
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from tabulate import tabulate
import redis.asyncio as redis

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from domains.shared.models.conversation_state import (
    ConversationState,
    ConversationMessage,
    ConversationContext,
    ConversationStatus,
    MessageRole
)
from infrastructure.messaging.state_manager import (
    RedisConversationStateManager,
    ConversationContextManager,
    ConversationStateManagerFactory
)
from infrastructure.messaging.state_recovery import (
    StateRecoveryFactory,
    BackupType,
    RecoveryStatus
)
from infrastructure.persistence.cache.session_store import SessionStoreFactory


class StateInspectorCLI:
    """Command-line interface for state inspection and debugging"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize state inspector with Redis connection"""
        self.redis_url = redis_url
        self.redis_client = None
        self.state_manager = None
        self.context_manager = None
        self.recovery_manager = None
        self.session_store = None
    
    async def connect(self):
        """Establish connections to Redis and create managers"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Create managers
            self.session_store = SessionStoreFactory.create_redis_session_store(self.redis_client)
            self.state_manager = ConversationStateManagerFactory.create_redis_manager(self.session_store)
            self.context_manager = ConversationStateManagerFactory.create_context_manager(self.state_manager)
            self.recovery_manager = StateRecoveryFactory.create_recovery_manager(self.redis_client)
            
            print(f"✅ Connected to Redis: {self.redis_url}")
            
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.aclose()
    
    async def list_conversations(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        detailed: bool = False
    ):
        """List conversations with optional filtering"""
        print("\n🔍 Listing Conversations")
        print("=" * 50)
        
        try:
            if user_id:
                # Get conversations for specific user
                conversations = await self.state_manager.get_user_conversations(
                    user_id,
                    ConversationStatus(status) if status else None,
                    limit
                )
            else:
                # Get all conversations by scanning Redis keys
                conversations = await self._scan_all_conversations(status, limit)
            
            if not conversations:
                print("No conversations found.")
                return
            
            # Prepare table data
            if detailed:
                headers = [
                    "Conversation ID", "User ID", "Status", "Messages", 
                    "Tokens", "Created", "Last Activity", "Duration"
                ]
                table_data = []
                
                for conv in conversations:
                    duration = (conv.last_activity_at - conv.created_at).total_seconds()
                    duration_str = self._format_duration(duration)
                    
                    table_data.append([
                        conv.conversation_id[:12] + "...",
                        conv.user_id[:15] + ("..." if len(conv.user_id) > 15 else ""),
                        conv.status.value,
                        len(conv.messages),
                        conv.total_tokens_used,
                        conv.created_at.strftime("%Y-%m-%d %H:%M"),
                        conv.last_activity_at.strftime("%Y-%m-%d %H:%M"),
                        duration_str
                    ])
            else:
                headers = ["Conversation ID", "User ID", "Status", "Messages", "Last Activity"]
                table_data = []
                
                for conv in conversations:
                    table_data.append([
                        conv.conversation_id[:16] + "...",
                        conv.user_id[:20] + ("..." if len(conv.user_id) > 20 else ""),
                        conv.status.value,
                        len(conv.messages),
                        conv.last_activity_at.strftime("%Y-%m-%d %H:%M")
                    ])
            
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            print(f"\nTotal conversations: {len(conversations)}")
            
        except Exception as e:
            print(f"❌ Error listing conversations: {e}")
    
    async def inspect_conversation(
        self,
        conversation_id: str,
        show_messages: bool = True,
        show_context: bool = True,
        show_metadata: bool = False,
        validate: bool = True
    ):
        """Inspect a specific conversation in detail"""
        print(f"\n🔍 Inspecting Conversation: {conversation_id}")
        print("=" * 60)
        
        try:
            conversation = await self.state_manager.get_conversation(conversation_id)
            
            if not conversation:
                print("❌ Conversation not found.")
                return
            
            # Basic information
            print(f"📋 Basic Information:")
            print(f"   Conversation ID: {conversation.conversation_id}")
            print(f"   User ID: {conversation.user_id}")
            print(f"   Session ID: {conversation.session_id or 'None'}")
            print(f"   Status: {conversation.status.value}")
            print(f"   Title: {conversation.title or 'None'}")
            print(f"   Tags: {', '.join(conversation.tags) if conversation.tags else 'None'}")
            
            # Timestamps
            print(f"\n📅 Timestamps:")
            print(f"   Created: {conversation.created_at}")
            print(f"   Updated: {conversation.updated_at}")
            print(f"   Last Activity: {conversation.last_activity_at}")
            
            duration = (conversation.last_activity_at - conversation.created_at).total_seconds()
            print(f"   Duration: {self._format_duration(duration)}")
            
            # Token information
            print(f"\n🎯 Token Information:")
            print(f"   Total Tokens Used: {conversation.total_tokens_used}")
            print(f"   Token Limit: {conversation.token_limit or 'None'}")
            
            if conversation.token_limit:
                usage_pct = (conversation.total_tokens_used / conversation.token_limit) * 100
                print(f"   Token Usage: {usage_pct:.1f}%")
                print(f"   Near Limit: {'Yes' if conversation.is_near_token_limit() else 'No'}")
            
            # Messages
            if show_messages:
                print(f"\n💬 Messages ({len(conversation.messages)}):")
                if conversation.messages:
                    for i, msg in enumerate(conversation.messages, 1):
                        print(f"\n   Message {i}:")
                        print(f"     ID: {msg.message_id}")
                        print(f"     Role: {msg.role.value}")
                        print(f"     Timestamp: {msg.timestamp}")
                        print(f"     Tokens: {msg.tokens_used or 'N/A'}")
                        print(f"     Content: {self._truncate_text(msg.content, 100)}")
                        
                        if msg.metadata and show_metadata:
                            print(f"     Metadata: {json.dumps(msg.metadata, indent=6)}")
                else:
                    print("     No messages found.")
            
            # Context
            if show_context:
                print(f"\n⚙️  Context:")
                print(f"   User Preferences: {json.dumps(conversation.context.user_preferences, indent=4)}")
                print(f"   Conversation Settings: {json.dumps(conversation.context.conversation_settings, indent=4)}")
                print(f"   Domain Context: {json.dumps(conversation.context.domain_context, indent=4)}")
                print(f"   Session Metadata: {json.dumps(conversation.context.session_metadata, indent=4)}")
            
            # General metadata
            if show_metadata and conversation.metadata:
                print(f"\n📊 Metadata:")
                print(f"   {json.dumps(conversation.metadata, indent=4)}")
            
            # Validation
            if validate:
                print(f"\n✅ Validation:")
                corruption_detector = StateRecoveryFactory.create_basic_corruption_detector()
                is_valid, errors = await corruption_detector.validate_state(conversation)
                
                if is_valid:
                    print("   State is valid ✅")
                else:
                    print(f"   State has issues ❌")
                    for error in errors:
                        print(f"     - {error}")
                
                # Check for corruption
                is_corrupted, issues = await corruption_detector.detect_corruption(
                    conversation_id, conversation
                )
                
                if is_corrupted:
                    print(f"   Potential corruption detected ⚠️")
                    for issue in issues:
                        print(f"     - {issue}")
                else:
                    print("   No corruption detected ✅")
            
        except Exception as e:
            print(f"❌ Error inspecting conversation: {e}")
    
    async def search_conversations(
        self,
        query: str,
        search_type: str = "content",
        user_id: Optional[str] = None,
        limit: int = 20
    ):
        """Search conversations by content, user, or metadata"""
        print(f"\n🔍 Searching Conversations: '{query}' (type: {search_type})")
        print("=" * 60)
        
        try:
            # Get conversations to search
            if user_id:
                conversations = await self.state_manager.get_user_conversations(user_id, limit=100)
            else:
                conversations = await self._scan_all_conversations(limit=100)
            
            matches = []
            
            for conv in conversations:
                if search_type == "content":
                    # Search in message content
                    for msg in conv.messages:
                        if query.lower() in msg.content.lower():
                            matches.append((conv, f"Message: {self._truncate_text(msg.content, 50)}"))
                            break
                
                elif search_type == "user":
                    if query.lower() in conv.user_id.lower():
                        matches.append((conv, f"User ID: {conv.user_id}"))
                
                elif search_type == "metadata":
                    # Search in metadata
                    metadata_str = json.dumps(conv.metadata).lower()
                    if query.lower() in metadata_str:
                        matches.append((conv, f"Metadata match"))
                
                elif search_type == "tags":
                    if any(query.lower() in tag.lower() for tag in conv.tags):
                        matching_tags = [tag for tag in conv.tags if query.lower() in tag.lower()]
                        matches.append((conv, f"Tags: {', '.join(matching_tags)}"))
                
                if len(matches) >= limit:
                    break
            
            if not matches:
                print("No matches found.")
                return
            
            # Display results
            headers = ["Conversation ID", "User ID", "Status", "Match", "Last Activity"]
            table_data = []
            
            for conv, match_info in matches:
                table_data.append([
                    conv.conversation_id[:16] + "...",
                    conv.user_id[:15] + ("..." if len(conv.user_id) > 15 else ""),
                    conv.status.value,
                    match_info,
                    conv.last_activity_at.strftime("%Y-%m-%d %H:%M")
                ])
            
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            print(f"\nFound {len(matches)} matches")
            
        except Exception as e:
            print(f"❌ Error searching conversations: {e}")
    
    async def analyze_conversation_health(self, conversation_id: str):
        """Analyze conversation health and provide recommendations"""
        print(f"\n🏥 Health Analysis: {conversation_id}")
        print("=" * 50)
        
        try:
            conversation = await self.state_manager.get_conversation(conversation_id)
            
            if not conversation:
                print("❌ Conversation not found.")
                return
            
            health_score = 100
            issues = []
            warnings = []
            recommendations = []
            
            # Check message count
            msg_count = len(conversation.messages)
            if msg_count > 1000:
                issues.append(f"Very high message count: {msg_count}")
                health_score -= 30
                recommendations.append("Consider archiving old messages or creating a new conversation")
            elif msg_count > 500:
                warnings.append(f"High message count: {msg_count}")
                health_score -= 10
                recommendations.append("Monitor conversation length")
            
            # Check token usage
            if conversation.token_limit:
                token_usage = conversation.total_tokens_used / conversation.token_limit
                if token_usage > 0.9:
                    issues.append(f"Near token limit: {token_usage*100:.1f}%")
                    health_score -= 25
                    recommendations.append("Conversation is near token limit - consider context window management")
                elif token_usage > 0.7:
                    warnings.append(f"High token usage: {token_usage*100:.1f}%")
                    health_score -= 10
            
            # Check conversation age
            age = (datetime.utcnow() - conversation.created_at).total_seconds()
            if age > 7 * 24 * 3600:  # 7 days
                warnings.append(f"Long-running conversation: {self._format_duration(age)}")
                health_score -= 5
                recommendations.append("Consider if this conversation should be archived")
            
            # Check inactivity
            inactivity = (datetime.utcnow() - conversation.last_activity_at).total_seconds()
            if inactivity > 24 * 3600:  # 24 hours
                warnings.append(f"Inactive for: {self._format_duration(inactivity)}")
                health_score -= 5
            
            # Check message patterns
            if msg_count > 0:
                user_msgs = sum(1 for msg in conversation.messages if msg.role == MessageRole.USER)
                assistant_msgs = sum(1 for msg in conversation.messages if msg.role == MessageRole.ASSISTANT)
                
                if user_msgs > 0:
                    ratio = assistant_msgs / user_msgs
                    if ratio < 0.5:
                        warnings.append(f"Low assistant response ratio: {ratio:.2f}")
                        health_score -= 5
                    elif ratio > 2.0:
                        warnings.append(f"High assistant response ratio: {ratio:.2f}")
                        health_score -= 5
            
            # Validate state
            corruption_detector = StateRecoveryFactory.create_basic_corruption_detector()
            is_valid, validation_errors = await corruption_detector.validate_state(conversation)
            
            if not is_valid:
                issues.extend(validation_errors)
                health_score -= 40
                recommendations.append("State validation failed - consider recovery from backup")
            
            # Display results
            print(f"🎯 Health Score: {max(0, health_score)}/100")
            
            if health_score >= 80:
                print("✅ Conversation health: GOOD")
            elif health_score >= 60:
                print("⚠️  Conversation health: FAIR")
            else:
                print("❌ Conversation health: POOR")
            
            if issues:
                print(f"\n❌ Issues ({len(issues)}):")
                for issue in issues:
                    print(f"   - {issue}")
            
            if warnings:
                print(f"\n⚠️  Warnings ({len(warnings)}):")
                for warning in warnings:
                    print(f"   - {warning}")
            
            if recommendations:
                print(f"\n💡 Recommendations:")
                for rec in recommendations:
                    print(f"   - {rec}")
            
            if not issues and not warnings:
                print("\n✅ No issues detected!")
            
        except Exception as e:
            print(f"❌ Error analyzing conversation health: {e}")
    
    async def export_conversation(
        self,
        conversation_id: str,
        output_file: str,
        format_type: str = "json"
    ):
        """Export conversation to file"""
        print(f"\n📤 Exporting Conversation: {conversation_id}")
        print(f"Output: {output_file} (format: {format_type})")
        print("=" * 50)
        
        try:
            conversation = await self.state_manager.get_conversation(conversation_id)
            
            if not conversation:
                print("❌ Conversation not found.")
                return
            
            if format_type == "json":
                with open(output_file, 'w') as f:
                    json.dump(conversation.dict(), f, indent=2, default=str)
            
            elif format_type == "txt":
                with open(output_file, 'w') as f:
                    f.write(f"Conversation Export\n")
                    f.write(f"=" * 50 + "\n\n")
                    f.write(f"ID: {conversation.conversation_id}\n")
                    f.write(f"User: {conversation.user_id}\n")
                    f.write(f"Status: {conversation.status.value}\n")
                    f.write(f"Created: {conversation.created_at}\n")
                    f.write(f"Messages: {len(conversation.messages)}\n")
                    f.write(f"Tokens: {conversation.total_tokens_used}\n\n")
                    
                    f.write("Messages:\n")
                    f.write("-" * 30 + "\n")
                    
                    for i, msg in enumerate(conversation.messages, 1):
                        f.write(f"\n[{i}] {msg.role.value.upper()} ({msg.timestamp})\n")
                        f.write(f"{msg.content}\n")
            
            else:
                print(f"❌ Unsupported format: {format_type}")
                return
            
            print(f"✅ Conversation exported to {output_file}")
            
        except Exception as e:
            print(f"❌ Error exporting conversation: {e}")
    
    async def show_statistics(self):
        """Show overall state management statistics"""
        print("\n📊 State Management Statistics")
        print("=" * 50)
        
        try:
            # Get all conversations
            conversations = await self._scan_all_conversations(limit=1000)
            
            if not conversations:
                print("No conversations found.")
                return
            
            # Calculate statistics
            total_conversations = len(conversations)
            total_messages = sum(len(conv.messages) for conv in conversations)
            total_tokens = sum(conv.total_tokens_used for conv in conversations)
            
            # Status distribution
            status_counts = {}
            for conv in conversations:
                status = conv.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # User distribution
            user_counts = {}
            for conv in conversations:
                user_id = conv.user_id
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
            
            # Time-based analysis
            now = datetime.utcnow()
            active_today = sum(1 for conv in conversations 
                             if (now - conv.last_activity_at).days == 0)
            active_week = sum(1 for conv in conversations 
                            if (now - conv.last_activity_at).days <= 7)
            
            # Display statistics
            print(f"📈 Overview:")
            print(f"   Total Conversations: {total_conversations}")
            print(f"   Total Messages: {total_messages}")
            print(f"   Total Tokens: {total_tokens:,}")
            print(f"   Average Messages/Conversation: {total_messages/total_conversations:.1f}")
            print(f"   Average Tokens/Conversation: {total_tokens/total_conversations:.1f}")
            
            print(f"\n📊 Status Distribution:")
            for status, count in sorted(status_counts.items()):
                percentage = (count / total_conversations) * 100
                print(f"   {status}: {count} ({percentage:.1f}%)")
            
            print(f"\n👥 User Activity:")
            print(f"   Unique Users: {len(user_counts)}")
            print(f"   Average Conversations/User: {total_conversations/len(user_counts):.1f}")
            
            print(f"\n📅 Activity:")
            print(f"   Active Today: {active_today}")
            print(f"   Active This Week: {active_week}")
            
            # Top users
            if len(user_counts) > 0:
                top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                print(f"\n🏆 Top Users:")
                for user_id, count in top_users:
                    user_display = user_id[:20] + ("..." if len(user_id) > 20 else "")
                    print(f"   {user_display}: {count} conversations")
            
        except Exception as e:
            print(f"❌ Error generating statistics: {e}")
    
    async def _scan_all_conversations(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[ConversationState]:
        """Scan Redis for all conversations"""
        conversations = []
        
        try:
            # Scan for conversation keys
            pattern = f"{self.state_manager.key_prefix}*"
            count = 0
            
            async for key in self.redis_client.scan_iter(match=pattern, count=50):
                if count >= limit:
                    break
                
                key_str = key.decode() if isinstance(key, bytes) else key
                conversation_id = key_str[len(self.state_manager.key_prefix):]
                
                conversation = await self.state_manager.get_conversation(conversation_id)
                if conversation:
                    if status is None or conversation.status.value == status:
                        conversations.append(conversation)
                        count += 1
            
            return conversations
            
        except Exception as e:
            print(f"❌ Error scanning conversations: {e}")
            return []
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m"
        elif seconds < 86400:
            return f"{int(seconds/3600)}h"
        else:
            return f"{int(seconds/86400)}d"
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="State Inspector - Debug tool for conversation states")
    parser.add_argument("--redis-url", default="redis://localhost:6379/0", help="Redis connection URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List conversations")
    list_parser.add_argument("--user-id", help="Filter by user ID")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--limit", type=int, default=50, help="Limit results")
    list_parser.add_argument("--detailed", action="store_true", help="Show detailed information")
    
    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect specific conversation")
    inspect_parser.add_argument("conversation_id", help="Conversation ID to inspect")
    inspect_parser.add_argument("--no-messages", action="store_true", help="Hide messages")
    inspect_parser.add_argument("--no-context", action="store_true", help="Hide context")
    inspect_parser.add_argument("--show-metadata", action="store_true", help="Show metadata")
    inspect_parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search conversations")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--type", choices=["content", "user", "metadata", "tags"], 
                              default="content", help="Search type")
    search_parser.add_argument("--user-id", help="Limit search to specific user")
    search_parser.add_argument("--limit", type=int, default=20, help="Limit results")
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Analyze conversation health")
    health_parser.add_argument("conversation_id", help="Conversation ID to analyze")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export conversation")
    export_parser.add_argument("conversation_id", help="Conversation ID to export")
    export_parser.add_argument("output_file", help="Output file path")
    export_parser.add_argument("--format", choices=["json", "txt"], default="json", help="Export format")
    
    # Stats command
    subparsers.add_parser("stats", help="Show statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize inspector
    inspector = StateInspectorCLI(args.redis_url)
    
    try:
        await inspector.connect()
        
        # Execute command
        if args.command == "list":
            await inspector.list_conversations(
                user_id=args.user_id,
                status=args.status,
                limit=args.limit,
                detailed=args.detailed
            )
        
        elif args.command == "inspect":
            await inspector.inspect_conversation(
                conversation_id=args.conversation_id,
                show_messages=not args.no_messages,
                show_context=not args.no_context,
                show_metadata=args.show_metadata,
                validate=not args.no_validate
            )
        
        elif args.command == "search":
            await inspector.search_conversations(
                query=args.query,
                search_type=args.type,
                user_id=args.user_id,
                limit=args.limit
            )
        
        elif args.command == "health":
            await inspector.analyze_conversation_health(args.conversation_id)
        
        elif args.command == "export":
            await inspector.export_conversation(
                conversation_id=args.conversation_id,
                output_file=args.output_file,
                format_type=args.format
            )
        
        elif args.command == "stats":
            await inspector.show_statistics()
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await inspector.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")