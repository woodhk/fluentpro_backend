from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, List, Any, Optional
import json
from django.conf import settings


class ConversationFlowService:
    """
    Service for managing Phase 2 onboarding conversation flow using LangChain
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-2024-11-20",  # Using latest GPT-4 model
            api_key=settings.OPENAI_API_KEY,
            temperature=0.7
        )
        
        # Conversation state tracking
        self.current_step = 1
        self.conversation_history = []
        self.communication_partners = []
        self.work_situations = {}
        
    def create_system_prompt(self, user_name: str, role: str, industry: str, native_language: str) -> str:
        """
        Create the system prompt for the conversation
        """
        return f"""You are a professional business English consultant trying to uncover the English workplace speaking needs for a {role} in the {industry} industry.

Your task is to conduct a conversation in {native_language} following these steps:

1. Initial Greeting: Greet {user_name} by name and ask how their day is
2. State Purpose: Explain the purpose of this conversation and confirm they're ready
3. Communication Partners: Ask who they typically speak English with at work (Clients? Customers? Colleagues? Suppliers? Partners? Senior Management? Stakeholders? Other?)
4. Work Situations: For each communication partner mentioned, discover what situations they need to speak English in (Meetings? Negotiations? Presentations? Consultations? Interviews? Other?)
5. Repeat for all communication partners

Important guidelines:
- Always acknowledge what the user said
- Keep an enthusiastic, supportive tone but remain professional
- Speak in {native_language}
- Focus on VERBAL/SPOKEN communication in English, NOT writing
- Ask follow-up questions to ensure completeness
- When you determine the conversation is finished, respond with exactly "CONVERSATION_FINISHED"

Current conversation step: You will be told which step you're on."""

    def get_step_prompt(self, step: int, user_name: str, context: Dict = None) -> str:
        """
        Get the prompt for the current conversation step
        """
        prompts = {
            1: f"Start with Step 1: Initial Greeting. Greet {user_name} by name and ask how their day is. Be warm and friendly.",
            
            2: "Move to Step 2: State the purpose of this conversation - to understand their English workplace speaking needs - and confirm they're ready to begin.",
            
            3: "Move to Step 3: Ask about Communication Partners. Find out who they typically speak English with at work. Provide examples like: Clients, Customers, Colleagues, Suppliers, Partners, Senior Management, Stakeholders, or others.",
            
            4: f"Move to Step 4: Work Situations. Ask about specific work situations where they need to speak English with {context.get('current_partner', 'the communication partners they mentioned')}. Provide examples like: Meetings, Negotiations, Presentations, Consultations, Interviews, or other situations.",
            
            5: "Continue exploring work situations for the next communication partner, or if all partners have been covered, summarize what you've learned and determine if the conversation is complete."
        }
        
        return prompts.get(step, "Continue the conversation naturally based on the user's responses.")

    def process_message(self, user_message: str, user_name: str, role: str, industry: str, native_language: str, conversation_state: Dict = None) -> Dict[str, Any]:
        """
        Process a user message and return AI response with updated state
        """
        if conversation_state is None:
            conversation_state = {
                'step': 1,
                'communication_partners': [],
                'work_situations': {},
                'conversation_history': []
            }
        
        # Add user message to history
        conversation_state['conversation_history'].append({
            'type': 'user',
            'content': user_message,
            'timestamp': self._get_timestamp()
        })
        
        # Create system prompt
        system_prompt = self.create_system_prompt(user_name, role, industry, native_language)
        
        # Get step-specific prompt
        step_prompt = self.get_step_prompt(conversation_state['step'], user_name, conversation_state)
        
        # Build conversation history for context
        history_context = self._build_history_context(conversation_state['conversation_history'])
        
        # Create the full prompt
        full_prompt = f"""
{system_prompt}

{step_prompt}

Previous conversation context:
{history_context}

User's latest message: {user_message}

Respond appropriately in {native_language}. If you determine the conversation is complete, respond with exactly "CONVERSATION_FINISHED".
"""
        
        try:
            # Get AI response
            response = self.llm.invoke([SystemMessage(content=full_prompt)])
            ai_response = response.content
            
            # Check if conversation is finished
            is_finished = "CONVERSATION_FINISHED" in ai_response
            
            if is_finished:
                ai_response = "conversation finished"
            
            # Add AI response to history
            conversation_state['conversation_history'].append({
                'type': 'ai',
                'content': ai_response,
                'timestamp': self._get_timestamp()
            })
            
            # Update conversation state based on response and step
            conversation_state = self._update_conversation_state(
                conversation_state, user_message, ai_response
            )
            
            return {
                'success': True,
                'ai_response': ai_response,
                'conversation_state': conversation_state,
                'is_finished': is_finished,
                'current_step': conversation_state['step']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Conversation error: {str(e)}',
                'conversation_state': conversation_state
            }
    
    def _build_history_context(self, history: List[Dict]) -> str:
        """
        Build context string from conversation history
        """
        context_lines = []
        for message in history[-6:]:  # Last 6 messages for context
            speaker = "User" if message['type'] == 'user' else "AI"
            context_lines.append(f"{speaker}: {message['content']}")
        
        return "\n".join(context_lines)
    
    def _update_conversation_state(self, state: Dict, user_message: str, ai_response: str) -> Dict:
        """
        Update conversation state based on the current interaction
        """
        # Simple state progression logic
        current_step = state['step']
        
        # Progress to next step based on content and current step
        if current_step == 1 and any(word in user_message.lower() for word in ['good', 'fine', 'well', 'great', 'ok']):
            state['step'] = 2
        elif current_step == 2 and any(word in user_message.lower() for word in ['yes', 'ready', 'sure', 'ok']):
            state['step'] = 3
        elif current_step == 3 and len(user_message.strip()) > 10:  # User provided communication partners
            # Extract mentioned partners (simplified)
            partners = self._extract_communication_partners(user_message)
            state['communication_partners'].extend(partners)
            state['step'] = 4
        elif current_step == 4:
            # User provided work situations
            if state['communication_partners']:
                current_partner = state['communication_partners'][0] if state['communication_partners'] else 'general'
                situations = self._extract_work_situations(user_message)
                state['work_situations'][current_partner] = situations
                
                # Check if we need to ask about more partners
                if len(state['communication_partners']) > 1:
                    state['communication_partners'].pop(0)  # Remove processed partner
                    # Stay in step 4 for next partner
                else:
                    state['step'] = 5  # Move to conclusion
        
        return state
    
    def _extract_communication_partners(self, message: str) -> List[str]:
        """
        Extract communication partners from user message (simplified)
        """
        partners = []
        partner_keywords = {
            'clients': ['client', 'customer'],
            'colleagues': ['colleague', 'coworker', 'team'],
            'management': ['manager', 'boss', 'senior', 'management'],
            'stakeholders': ['stakeholder', 'investor'],
            'suppliers': ['supplier', 'vendor'],
            'partners': ['partner', 'external']
        }
        
        message_lower = message.lower()
        for partner, keywords in partner_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                partners.append(partner)
        
        return partners if partners else ['general']
    
    def _extract_work_situations(self, message: str) -> List[str]:
        """
        Extract work situations from user message (simplified)
        """
        situations = []
        situation_keywords = {
            'meetings': ['meeting', 'conference'],
            'presentations': ['presentation', 'present'],
            'negotiations': ['negotiation', 'negotiate'],
            'consultations': ['consultation', 'consult'],
            'interviews': ['interview'],
            'calls': ['call', 'phone']
        }
        
        message_lower = message.lower()
        for situation, keywords in situation_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                situations.append(situation)
        
        return situations if situations else ['general_communication']
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp
        """
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def start_conversation(self, user_name: str, role: str, industry: str, native_language: str) -> Dict[str, Any]:
        """
        Start a new conversation
        """
        initial_state = {
            'step': 1,
            'communication_partners': [],
            'work_situations': {},
            'conversation_history': []
        }
        
        # Generate initial greeting
        return self.process_message("Hello", user_name, role, industry, native_language, initial_state)