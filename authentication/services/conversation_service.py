from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, List, Any, Optional
import json
import re
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
        
        # Evaluator LLM for checking completeness
        self.evaluator_llm = ChatOpenAI(
            model="gpt-4o-2024-11-20",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1  # Lower temperature for more consistent evaluation
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
4. Work Situations: For each communication partner mentioned, discover what situations they need to speak English in (Meetings? Negotiations? Presentations? Consultations? Interviews? Phone calls? Customer complaints? Training sessions? Other?)
5. Repeat for all communication partners

CRITICAL: Follow-up questions should verify COMPLETENESS, not explore details.
- When they mention situations (e.g., "meetings"), ask "Are there any OTHER situations where you speak English with [partner] that you haven't mentioned yet?"
- Provide examples of other possible situations to jog their memory
- Don't ask for more details about situations they already mentioned
- Goal: Ensure you've captured ALL situations, not deeper information about each one

Important guidelines:
- Always acknowledge what the user said
- Keep an enthusiastic, supportive tone but remain professional
- Speak in {native_language}
- Focus on VERBAL/SPOKEN communication in English, NOT writing
- Ask follow-up questions to ensure completeness, not for more detail
- When you determine the conversation is finished, respond with exactly "CONVERSATION_FINISHED"

Current conversation step: You will be told which step you're on."""

    def get_step_prompt(self, step: int, user_name: str, context: Dict = None) -> str:
        """
        Get the prompt for the current conversation step
        """
        if context is None:
            context = {}
            
        current_partner = context.get('current_partner_being_asked', 'the communication partners')
        all_partners = context.get('all_partners_mentioned', [])
        partners_covered = context.get('partners_covered', [])
        
        prompts = {
            1: f"Start with Step 1: Initial Greeting. Greet {user_name} by name and ask how their day is. Be warm and friendly.",
            
            2: "Move to Step 2: State the purpose of this conversation - to understand their English workplace speaking needs - and confirm they're ready to begin.",
            
            3: "Move to Step 3: Ask about Communication Partners. Find out who they typically speak English with at work. Provide examples like: Clients, Customers, Colleagues, Suppliers, Partners, Senior Management, Stakeholders, or others.",
            
            4: f"""Move to Step 4: Work Situations. 
            
            CURRENT FOCUS: Ask about work situations for '{current_partner}'.
            
            ALL PARTNERS MENTIONED: {all_partners}
            PARTNERS ALREADY COVERED: {partners_covered}
            
            For {current_partner}, ask what specific situations they speak English in. After they respond, follow up to VERIFY COMPLETENESS by asking if there are any OTHER situations they haven't mentioned yet. Provide examples of different situations like: Meetings, Negotiations, Presentations, Consultations, Interviews, Phone calls, Customer complaints, Training sessions, etc. 
            
            The goal is to ensure you've captured ALL situations for {current_partner}, not to go deeper into the ones they already mentioned.""",
            
            5: f"""All communication partners have been covered! 
            
            PARTNERS COVERED: {partners_covered}
            WORK SITUATIONS COLLECTED: {context.get('work_situations', {})}
            
            Summarize what you've learned and determine if the conversation is complete. If you feel you have comprehensive information about all their English speaking needs, you can end the conversation."""
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
            
            # If conversation is finished, analyze and extract final summary
            if is_finished:
                print("🔍 Debug: Conversation finished, analyzing for summary...")
                analysis = self.analyze_conversation_for_summary(conversation_state['conversation_history'])
                conversation_state['final_analysis'] = analysis
                print(f"🔍 Debug: Final analysis: {analysis}")
            
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
        Update conversation state with proper partner transition handling
        """
        current_step = state['step']
        current_partner = state.get('current_partner_being_asked')
        partner_sub_state = state.get('partner_sub_state', 'initial')
        waiting_for_completeness = state.get('waiting_for_completeness_response', False)
        
        print(f"🔍 Debug State: step={current_step}, partner={current_partner}, sub_state={partner_sub_state}, waiting_completeness={waiting_for_completeness}")
        
        # Step 1: Initial greeting
        if current_step == 1 and any(word in user_message.lower() for word in ['good', 'fine', 'well', 'great', 'ok', 'hi']):
            state['step'] = 2
            
        # Step 2: Ready to proceed or partners mentioned
        elif current_step == 2:
            if any(word in user_message.lower() for word in ['yes', 'ready', 'sure', 'ok', 'yep', 'yeah']):
                state['step'] = 3
            elif any(word in user_message.lower() for word in ['client', 'colleague', 'management', 'stakeholder', 'customer', 'supplier']):
                partners = self.extract_communication_partners(user_message)
                if partners:
                    for partner in partners:
                        if partner not in state['all_partners_mentioned']:
                            state['all_partners_mentioned'].append(partner)
                    
                    print(f"🔍 Debug: Extracted partners: {partners}")
                    print(f"🔍 Debug: All partners mentioned: {state['all_partners_mentioned']}")
                    
                    state['step'] = 4
                    state['current_partner_being_asked'] = state['all_partners_mentioned'][0]
                    state['partner_sub_state'] = 'collecting'
            
        # Step 3: Communication partners mentioned
        elif current_step == 3 and len(user_message.strip()) > 5:
            partners = self.extract_communication_partners(user_message)
            
            for partner in partners:
                if partner not in state['all_partners_mentioned']:
                    state['all_partners_mentioned'].append(partner)
            
            print(f"🔍 Debug: Extracted partners: {partners}")
            print(f"🔍 Debug: All partners mentioned: {state['all_partners_mentioned']}")
            
            if partners:
                state['step'] = 4
                state['current_partner_being_asked'] = state['all_partners_mentioned'][0]
                state['partner_sub_state'] = 'collecting'
            
        # Step 4: Work situations collection with proper partner tracking
        elif current_step == 4 and current_partner:
            
            # Check if this response contains work situations
            has_situations = any(word in user_message.lower() for word in ['meeting', 'presentation', 'call', 'negotiation', 'consultation', 'review', 'training'])
            
            if has_situations:
                # Extract and add situations to the CURRENT partner (not the next one!)
                situations = self._extract_work_situations(user_message)
                if situations:
                    # Always add to current partner, extending existing list if any
                    existing_situations = state['work_situations'].get(current_partner, [])
                    all_situations = existing_situations + [s for s in situations if s not in existing_situations]
                    state['work_situations'][current_partner] = all_situations
                    
                    print(f"🔍 Debug: Added situations for {current_partner}: {situations}")
                    print(f"🔍 Debug: Total situations for {current_partner}: {all_situations}")
                    
                    # Set waiting for completeness verification
                    state['waiting_for_completeness_response'] = True
                    state['partner_sub_state'] = 'verifying_completeness'
            
            # Handle completeness responses ("no", "not really", etc.)
            elif waiting_for_completeness and user_message.lower().strip() in ['no', 'nope', 'nothing', 'not really', 'that\'s it', 'none', 'that\'s all']:
                # Current partner is complete, mark as covered
                if current_partner not in state['partners_covered']:
                    state['partners_covered'].append(current_partner)
                
                print(f"🔍 Debug: Partner {current_partner} marked as complete")
                print(f"🔍 Debug: Partners covered: {state['partners_covered']}")
                
                # Check if all partners have been covered
                evaluation = self.evaluate_conversation_completeness(state)
                print(f"🔍 Debug: Evaluation result: {evaluation}")
                
                if evaluation['all_covered']:
                    state['step'] = 5
                    state['current_partner_being_asked'] = None
                    state['partner_sub_state'] = 'initial'
                    state['waiting_for_completeness_response'] = False
                else:
                    # Move to next partner
                    next_partner = evaluation.get('next_partner_to_ask')
                    if next_partner:
                        state['current_partner_being_asked'] = next_partner
                        state['partner_sub_state'] = 'collecting'
                        state['waiting_for_completeness_response'] = False
                        print(f"🔍 Debug: Moving to next partner: {next_partner}")
                    else:
                        state['step'] = 5
                        state['current_partner_being_asked'] = None
                        state['partner_sub_state'] = 'initial'
                        state['waiting_for_completeness_response'] = False
        
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
    
    def extract_communication_partners(self, user_message: str) -> List[str]:
        """
        Use LLM to extract communication partners from user message
        """
        extract_prompt = f"""
        Extract all communication partners mentioned in this message. Return ONLY a JSON list of partners.
        
        Message: "{user_message}"
        
        Possible partners include: clients, customers, colleagues, coworkers, team members, suppliers, vendors, partners, senior management, managers, stakeholders, investors, external partners, etc.
        
        Return format: ["partner1", "partner2", "partner3"]
        """
        
        try:
            response = self.evaluator_llm.invoke([SystemMessage(content=extract_prompt)])
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', response.content)
            if json_match:
                partners = json.loads(json_match.group())
                return [p.lower().strip() for p in partners if p.strip()]
            return []
        except Exception as e:
            print(f"Error extracting partners: {e}")
            return self._extract_communication_partners(user_message)  # Fallback to simple method

    def evaluate_conversation_completeness(self, conversation_state: Dict) -> Dict[str, Any]:
        """
        Use evaluator LLM to check if all communication partners have been covered
        """
        partners_mentioned = conversation_state.get('all_partners_mentioned', [])
        partners_covered = list(conversation_state.get('work_situations', {}).keys())
        
        evaluation_prompt = f"""
        You are evaluating whether a conversation has covered all communication partners.
        
        Partners mentioned by user: {partners_mentioned}
        Partners we've asked about work situations: {partners_covered}
        
        TASK: Determine if there are any partners mentioned by the user that we haven't asked about work situations yet.
        
        Return your response in this exact JSON format:
        {{
            "all_covered": true/false,
            "missing_partners": ["partner1", "partner2"],
            "next_partner_to_ask": "partner_name" or null
        }}
        
        Rules:
        - "all_covered" should be true ONLY if every partner mentioned has been asked about
        - "missing_partners" should list partners mentioned but not yet asked about
        - "next_partner_to_ask" should be the first missing partner, or null if all covered
        """
        
        try:
            response = self.evaluator_llm.invoke([SystemMessage(content=evaluation_prompt)])
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
                return evaluation
            return {"all_covered": False, "missing_partners": [], "next_partner_to_ask": None}
        except Exception as e:
            print(f"Error in evaluation: {e}")
            # Fallback logic
            missing = [p for p in partners_mentioned if p not in partners_covered]
            return {
                "all_covered": len(missing) == 0,
                "missing_partners": missing,
                "next_partner_to_ask": missing[0] if missing else None
            }

    def analyze_conversation_for_summary(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Use LLM to analyze conversation history and extract communication partners and work situations
        """
        # Build conversation text
        conversation_text = ""
        for msg in conversation_history:
            speaker = "User" if msg['type'] == 'user' else "AI"
            conversation_text += f"{speaker}: {msg['content']}\n"
        
        analysis_prompt = f"""
        Analyze this conversation and extract the communication partners and work situations mentioned.
        
        CONVERSATION:
        {conversation_text}
        
        TASK: Extract all communication partners and their associated work situations from this conversation.
        
        Return your response in this exact JSON format:
        {{
            "communication_partners": ["partner1", "partner2", "partner3"],
            "work_situations": {{
                "partner1": ["situation1", "situation2"],
                "partner2": ["situation1", "situation3"],
                "partner3": ["situation1"]
            }}
        }}
        
        Rules:
        - Only include partners that were explicitly mentioned by the user
        - Only include work situations that were explicitly mentioned by the user
        - Use consistent naming (e.g., "clients", "senior management", "stakeholders")
        - Include all situations mentioned for each partner
        """
        
        try:
            response = self.evaluator_llm.invoke([SystemMessage(content=analysis_prompt)])
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
            return {"communication_partners": [], "work_situations": {}}
        except Exception as e:
            print(f"Error in conversation analysis: {e}")
            return {"communication_partners": [], "work_situations": {}}

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
            'all_partners_mentioned': [],  # Track all partners ever mentioned
            'partners_covered': [],  # Track partners we've asked about
            'work_situations': {},
            'conversation_history': [],
            'current_partner_being_asked': None,
            'partner_sub_state': 'initial',  # 'initial', 'collecting', 'verifying_completeness'
            'waiting_for_completeness_response': False
        }
        
        # Generate initial greeting
        return self.process_message("Hello", user_name, role, industry, native_language, initial_state)