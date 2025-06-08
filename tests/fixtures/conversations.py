"""
Conversation state fixtures for testing state management and persistence.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from domains.shared.models.conversation_state import ConversationState, MessageState, ParticipantState


class ConversationFixtures:
    """Factory for creating test conversation states."""
    
    @staticmethod
    def create_conversation_state(
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: str = 'active',
        **kwargs
    ) -> ConversationState:
        """Create a basic conversation state with default values."""
        return ConversationState(
            conversation_id=conversation_id or str(uuid.uuid4()),
            user_id=user_id or str(uuid.uuid4()),
            status=status,
            context=kwargs.get('context', {}),
            metadata=kwargs.get('metadata', {}),
            created_at=kwargs.get('created_at', datetime.utcnow()),
            updated_at=kwargs.get('updated_at', datetime.utcnow()),
            expires_at=kwargs.get('expires_at', datetime.utcnow() + timedelta(hours=24))
        )
    
    @staticmethod
    def create_active_conversation() -> ConversationState:
        """Create an active conversation state."""
        return ConversationFixtures.create_conversation_state(
            status='active',
            context={
                'current_topic': 'business_meeting_preparation',
                'language_level': 'intermediate',
                'formality': 'business'
            },
            metadata={
                'session_type': 'practice',
                'goal': 'improve_presentation_skills'
            }
        )
    
    @staticmethod
    def create_paused_conversation() -> ConversationState:
        """Create a paused conversation state."""
        return ConversationFixtures.create_conversation_state(
            status='paused',
            context={
                'current_topic': 'customer_service_interaction',
                'language_level': 'advanced',
                'formality': 'professional',
                'pause_reason': 'user_request'
            },
            metadata={
                'session_type': 'role_play',
                'pause_timestamp': datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def create_completed_conversation() -> ConversationState:
        """Create a completed conversation state."""
        return ConversationFixtures.create_conversation_state(
            status='completed',
            context={
                'current_topic': 'team_leadership_discussion',
                'language_level': 'advanced',
                'formality': 'business',
                'completion_reason': 'goal_achieved'
            },
            metadata={
                'session_type': 'coaching',
                'completion_timestamp': datetime.utcnow().isoformat(),
                'success_metrics': {
                    'fluency_score': 8.5,
                    'confidence_level': 9.0,
                    'goal_completion': True
                }
            }
        )
    
    @staticmethod
    def create_error_conversation() -> ConversationState:
        """Create a conversation state with error status."""
        return ConversationFixtures.create_conversation_state(
            status='error',
            context={
                'current_topic': 'sales_negotiation',
                'language_level': 'intermediate',
                'formality': 'business',
                'error_type': 'ai_service_unavailable'
            },
            metadata={
                'session_type': 'simulation',
                'error_timestamp': datetime.utcnow().isoformat(),
                'error_details': {
                    'error_code': 'SERVICE_UNAVAILABLE',
                    'retry_count': 3,
                    'last_error_message': 'AI completion service is temporarily unavailable'
                }
            }
        )


class MessageFixtures:
    """Factory for creating test message states."""
    
    @staticmethod
    def create_message_state(
        message_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        sender_type: str = 'user',
        content: Optional[str] = None,
        **kwargs
    ) -> MessageState:
        """Create a basic message state with default values."""
        return MessageState(
            message_id=message_id or str(uuid.uuid4()),
            conversation_id=conversation_id or str(uuid.uuid4()),
            sender_type=sender_type,
            sender_id=kwargs.get('sender_id', str(uuid.uuid4())),
            content=content or f"Test message content {uuid.uuid4().hex[:8]}",
            message_type=kwargs.get('message_type', 'text'),
            metadata=kwargs.get('metadata', {}),
            timestamp=kwargs.get('timestamp', datetime.utcnow()),
            processed=kwargs.get('processed', False),
            processing_metadata=kwargs.get('processing_metadata', {})
        )
    
    @staticmethod
    def create_user_message(
        conversation_id: Optional[str] = None,
        content: Optional[str] = None
    ) -> MessageState:
        """Create a user message state."""
        return MessageFixtures.create_message_state(
            conversation_id=conversation_id,
            sender_type='user',
            content=content or "I need help preparing for my presentation to the board.",
            message_type='text',
            metadata={
                'input_method': 'text',
                'language_detected': 'en',
                'confidence_score': 0.95
            }
        )
    
    @staticmethod
    def create_ai_message(
        conversation_id: Optional[str] = None,
        content: Optional[str] = None
    ) -> MessageState:
        """Create an AI assistant message state."""
        return MessageFixtures.create_message_state(
            conversation_id=conversation_id,
            sender_type='assistant',
            content=content or "I'd be happy to help you prepare for your board presentation. Let's start by discussing your key objectives.",
            message_type='text',
            metadata={
                'model_used': 'gpt-4',
                'generation_time_ms': 1250,
                'confidence_score': 0.92,
                'prompt_tokens': 150,
                'completion_tokens': 45
            },
            processed=True,
            processing_metadata={
                'processing_time_ms': 85,
                'language_analysis': {
                    'formality_level': 'business',
                    'tone': 'helpful',
                    'complexity': 'moderate'
                }
            }
        )
    
    @staticmethod
    def create_system_message(
        conversation_id: Optional[str] = None,
        content: Optional[str] = None
    ) -> MessageState:
        """Create a system message state."""
        return MessageFixtures.create_message_state(
            conversation_id=conversation_id,
            sender_type='system',
            content=content or "Conversation started. Practice session: Business presentation skills.",
            message_type='system',
            metadata={
                'event_type': 'session_start',
                'automated': True
            },
            processed=True
        )


class ParticipantFixtures:
    """Factory for creating test participant states."""
    
    @staticmethod
    def create_participant_state(
        participant_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        participant_type: str = 'user',
        **kwargs
    ) -> ParticipantState:
        """Create a basic participant state with default values."""
        return ParticipantState(
            participant_id=participant_id or str(uuid.uuid4()),
            conversation_id=conversation_id or str(uuid.uuid4()),
            participant_type=participant_type,
            display_name=kwargs.get('display_name', f'Test {participant_type.title()}'),
            status=kwargs.get('status', 'active'),
            joined_at=kwargs.get('joined_at', datetime.utcnow()),
            last_activity=kwargs.get('last_activity', datetime.utcnow()),
            metadata=kwargs.get('metadata', {}),
            permissions=kwargs.get('permissions', ['read', 'write'])
        )
    
    @staticmethod
    def create_user_participant(
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ParticipantState:
        """Create a user participant state."""
        return ParticipantFixtures.create_participant_state(
            participant_id=user_id or str(uuid.uuid4()),
            conversation_id=conversation_id,
            participant_type='user',
            display_name='John Doe',
            metadata={
                'language_preference': 'en',
                'proficiency_level': 'intermediate',
                'role': 'manager',
                'industry': 'technology'
            },
            permissions=['read', 'write', 'manage']
        )
    
    @staticmethod
    def create_ai_participant(
        conversation_id: Optional[str] = None
    ) -> ParticipantState:
        """Create an AI assistant participant state."""
        return ParticipantFixtures.create_participant_state(
            participant_id=f"ai-{uuid.uuid4()}",
            conversation_id=conversation_id,
            participant_type='assistant',
            display_name='FluentPro AI Coach',
            metadata={
                'model_version': 'gpt-4',
                'specialization': 'business_communication',
                'capabilities': ['language_coaching', 'role_play', 'feedback']
            },
            permissions=['read', 'write']
        )


class ConversationScenarioFixtures:
    """Create complete conversation scenarios for testing."""
    
    @staticmethod
    def create_business_meeting_scenario() -> Dict[str, Any]:
        """Create a complete business meeting practice scenario."""
        conversation_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        conversation = ConversationFixtures.create_conversation_state(
            conversation_id=conversation_id,
            user_id=user_id,
            context={
                'current_topic': 'quarterly_business_review',
                'language_level': 'advanced',
                'formality': 'business',
                'scenario_type': 'meeting_facilitation'
            },
            metadata={
                'session_type': 'role_play',
                'goal': 'improve_meeting_leadership',
                'estimated_duration': 30
            }
        )
        
        participants = [
            ParticipantFixtures.create_user_participant(
                conversation_id=conversation_id,
                user_id=user_id
            ),
            ParticipantFixtures.create_ai_participant(
                conversation_id=conversation_id
            )
        ]
        
        messages = [
            MessageFixtures.create_system_message(
                conversation_id=conversation_id,
                content="Starting business meeting practice session. You are leading a quarterly business review."
            ),
            MessageFixtures.create_user_message(
                conversation_id=conversation_id,
                content="Good morning everyone, let's begin our Q3 review. I'd like to start with our sales performance."
            ),
            MessageFixtures.create_ai_message(
                conversation_id=conversation_id,
                content="Excellent opening! Your tone is confident and professional. Let's practice handling questions from stakeholders about the sales numbers."
            )
        ]
        
        return {
            'conversation': conversation,
            'participants': participants,
            'messages': messages,
            'scenario_type': 'business_meeting'
        }
    
    @staticmethod
    def create_customer_service_scenario() -> Dict[str, Any]:
        """Create a customer service interaction scenario."""
        conversation_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        conversation = ConversationFixtures.create_conversation_state(
            conversation_id=conversation_id,
            user_id=user_id,
            context={
                'current_topic': 'customer_complaint_resolution',
                'language_level': 'intermediate',
                'formality': 'professional',
                'scenario_type': 'customer_service'
            },
            metadata={
                'session_type': 'simulation',
                'goal': 'improve_conflict_resolution',
                'difficulty_level': 'medium'
            }
        )
        
        participants = [
            ParticipantFixtures.create_user_participant(
                conversation_id=conversation_id,
                user_id=user_id
            ),
            ParticipantFixtures.create_ai_participant(
                conversation_id=conversation_id
            )
        ]
        
        messages = [
            MessageFixtures.create_system_message(
                conversation_id=conversation_id,
                content="Customer service simulation: Handle an upset customer regarding a delayed order."
            ),
            MessageFixtures.create_ai_message(
                conversation_id=conversation_id,
                content="I'm really frustrated! My order was supposed to arrive three days ago and I haven't heard anything from your company!"
            ),
            MessageFixtures.create_user_message(
                conversation_id=conversation_id,
                content="I sincerely apologize for the delay and lack of communication. Let me look into your order immediately."
            )
        ]
        
        return {
            'conversation': conversation,
            'participants': participants,
            'messages': messages,
            'scenario_type': 'customer_service'
        }
    
    @staticmethod
    def create_presentation_practice_scenario() -> Dict[str, Any]:
        """Create a presentation practice scenario."""
        conversation_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        conversation = ConversationFixtures.create_conversation_state(
            conversation_id=conversation_id,
            user_id=user_id,
            context={
                'current_topic': 'product_launch_presentation',
                'language_level': 'advanced',
                'formality': 'business',
                'scenario_type': 'presentation_practice'
            },
            metadata={
                'session_type': 'coaching',
                'goal': 'improve_public_speaking',
                'audience_type': 'executives'
            }
        )
        
        participants = [
            ParticipantFixtures.create_user_participant(
                conversation_id=conversation_id,
                user_id=user_id
            ),
            ParticipantFixtures.create_ai_participant(
                conversation_id=conversation_id
            )
        ]
        
        messages = [
            MessageFixtures.create_system_message(
                conversation_id=conversation_id,
                content="Presentation coaching session: Practice delivering your product launch presentation to executives."
            ),
            MessageFixtures.create_user_message(
                conversation_id=conversation_id,
                content="Good morning, executives. Today I'm excited to present our new product that will revolutionize our market approach."
            ),
            MessageFixtures.create_ai_message(
                conversation_id=conversation_id,
                content="Strong start! Your enthusiasm comes through clearly. Now, try to add a compelling statistic or question to hook your audience even more."
            )
        ]
        
        return {
            'conversation': conversation,
            'participants': participants,
            'messages': messages,
            'scenario_type': 'presentation'
        }


def create_conversation_batch(count: int = 5) -> List[Dict[str, Any]]:
    """Create a batch of conversation scenarios for bulk testing."""
    scenarios = []
    scenario_types = [
        ConversationScenarioFixtures.create_business_meeting_scenario,
        ConversationScenarioFixtures.create_customer_service_scenario,
        ConversationScenarioFixtures.create_presentation_practice_scenario
    ]
    
    for i in range(count):
        scenario_func = scenario_types[i % len(scenario_types)]
        scenarios.append(scenario_func())
    
    return scenarios