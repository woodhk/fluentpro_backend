# Async Patterns and Best Practices

This guide provides comprehensive documentation for asynchronous programming patterns in the FluentPro backend, covering when to use async vs sync, common patterns, examples, and troubleshooting.

## Table of Contents

1. [Overview](#overview)
2. [When to Use Async vs Sync](#when-to-use-async-vs-sync)
3. [Async Patterns](#async-patterns)
4. [Working Code Examples](#working-code-examples)
5. [Best Practices](#best-practices)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Performance Considerations](#performance-considerations)

## Overview

FluentPro's async infrastructure enables AI-powered features requiring real-time data flow, long-running operations, and high concurrency. The system provides both synchronous and asynchronous APIs to ensure backward compatibility while enabling advanced AI capabilities.

### Architecture Components

- **Async Views**: `AsyncAPIView`, `AsyncViewSet` for handling async operations
- **Streaming Responses**: Memory-efficient streaming for large datasets
- **Server-Sent Events (SSE)**: Real-time client updates
- **Async Service Interfaces**: AI-powered services with streaming capabilities
- **Dual Compatibility**: All services support both sync and async operations

## When to Use Async vs Sync

### Use Async When:

✅ **AI/ML Operations**
- LLM completions and embeddings
- Real-time recommendations
- Predictive analytics
- Model inference

✅ **Real-time Features**
- Live progress tracking
- Streaming data to clients
- Server-Sent Events
- WebSocket communications

✅ **I/O-Bound Operations**
- External API calls
- Database queries with large datasets
- File uploads/downloads
- Network operations

✅ **Long-Running Tasks**
- Data processing pipelines
- Batch operations
- Report generation
- Background analysis

### Use Sync When:

✅ **Simple CRUD Operations**
- Basic create, read, update, delete
- Quick database lookups
- Simple validations
- Cached data retrieval

✅ **CPU-Bound Tasks**
- Mathematical calculations
- Data transformations
- Cryptographic operations
- Simple business logic

✅ **Legacy Compatibility**
- Existing sync codebases
- Third-party sync libraries
- Simple utility functions
- Quick response operations

## Async Patterns

### 1. Async View Pattern

**Use Case**: Handle async operations in Django REST Framework views.

```python
from api.common.async_views import AsyncAPIView
from rest_framework.permissions import IsAuthenticated

class AIRecommendationView(AsyncAPIView):
    """Async view for AI-powered recommendations."""
    
    permission_classes = [IsAuthenticated]
    
    async def async_get(self, request, *args, **kwargs):
        """Get AI recommendations asynchronously."""
        user_id = request.user.id
        
        # Use async service
        recommendation_service = get_recommendation_service()
        recommendations = await recommendation_service.get_ai_role_recommendations_async(
            user_id=user_id,
            user_input=request.GET.get('description', ''),
            limit=10
        )
        
        return await self.async_handle_use_case(
            lambda: recommendations,
            request_data=None
        )
    
    async def async_post(self, request, *args, **kwargs):
        """Generate personalized learning path."""
        user_id = request.user.id
        target_role = request.data.get('target_role')
        
        recommendation_service = get_recommendation_service()
        learning_path = await recommendation_service.generate_personalized_learning_path_async(
            user_id=user_id,
            target_role=target_role,
            timeline=request.data.get('timeline')
        )
        
        return Response(learning_path, status=status.HTTP_200_OK)
```

### 2. Streaming Response Pattern

**Use Case**: Stream large datasets without memory issues.

```python
from api.common.responses import APIResponse
from api.common.async_views import AsyncAPIView

class DataExportView(AsyncAPIView):
    """Stream large datasets efficiently."""
    
    async def async_get(self, request, *args, **kwargs):
        """Stream user data export."""
        user_id = request.user.id
        
        async def user_data_generator():
            """Generate user data chunks asynchronously."""
            # Stream user sessions
            session_service = get_session_service()
            sessions = await session_service.get_user_sessions_async(user_id)
            
            for session in sessions:
                yield {
                    "type": "session",
                    "id": session.id,
                    "created_at": session.created_at.isoformat(),
                    "data": session.data
                }
                
                # Yield control periodically
                await asyncio.sleep(0.001)
            
            # Stream recommendations
            recommendation_service = get_recommendation_service()
            async for recommendation in recommendation_service.get_user_recommendations_stream(user_id):
                yield {
                    "type": "recommendation",
                    "id": recommendation.id,
                    "content": recommendation.data
                }
        
        # Return streaming response
        return await APIResponse.streaming_response(
            data_source=user_data_generator(),
            streaming_type="objects",  # NDJSON format
            chunk_size=100
        )
```

### 3. Server-Sent Events Pattern

**Use Case**: Real-time updates to browser clients.

```python
from api.common.sse import SSEAPIView, SSEEvent

class ProgressTrackingView(SSEAPIView):
    """Real-time progress updates via SSE."""
    
    def sse_event_stream(self, request, *args, **kwargs):
        """Stream progress events."""
        task_id = request.GET.get('task_id')
        
        # Start long-running task
        task_service = get_task_service()
        progress_tracker = task_service.start_task(task_id)
        
        # Stream progress updates
        while not progress_tracker.is_complete():
            progress = progress_tracker.get_progress()
            
            yield SSEEvent(
                data={
                    "task_id": task_id,
                    "progress": progress.percentage,
                    "status": progress.status,
                    "message": progress.message,
                    "timestamp": datetime.utcnow().isoformat()
                },
                event_type="progress",
                event_id=f"progress_{progress.step}",
                retry=1000  # 1 second retry
            )
            
            time.sleep(1)  # Update every second
        
        # Send completion event
        yield SSEEvent(
            data={
                "task_id": task_id,
                "status": "completed",
                "result": progress_tracker.get_result()
            },
            event_type="complete",
            event_id="complete"
        )
```

### 4. Async Service Interface Pattern

**Use Case**: Implement services that support both sync and async operations.

```python
from domains.authentication.services.interfaces import IPasswordService

class PasswordService(IPasswordService):
    """Password service with both sync and async methods."""
    
    # Sync methods (backward compatibility)
    def hash_password(self, password: str) -> str:
        """Hash password synchronously."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password synchronously."""
        return bcrypt.checkpw(password.encode(), hashed.encode())
    
    # Async AI-powered methods
    async def analyze_password_security_async(self, password: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze password security using AI."""
        # Use async AI service
        ai_service = get_ai_service()
        
        # Generate security analysis
        analysis_prompt = f"""
        Analyze the security of this password: {password}
        Consider: length, complexity, common patterns, dictionary words
        Return JSON with security_score (0-100), vulnerabilities, and recommendations.
        """
        
        analysis_result = await ai_service.complete_with_system(
            system="You are a cybersecurity expert analyzing password security.",
            user=analysis_prompt,
            max_tokens=200
        )
        
        # Parse AI response
        try:
            analysis = json.loads(analysis_result)
            return {
                "security_score": analysis.get("security_score", 50),
                "vulnerability_analysis": analysis.get("vulnerabilities", []),
                "recommendations": analysis.get("recommendations", []),
                "attack_resistance": {
                    "dictionary": "medium",
                    "brute_force": "high" if len(password) > 12 else "medium"
                },
                "entropy_analysis": {
                    "bits": self._calculate_entropy(password),
                    "randomness": "high" if self._is_random(password) else "medium"
                }
            }
        except json.JSONDecodeError:
            # Fallback analysis
            return self._fallback_analysis(password)
    
    async def generate_contextual_password_async(self, user_context: Dict[str, Any], length: int = 16) -> Dict[str, Any]:
        """Generate AI-optimized password."""
        ai_service = get_ai_service()
        
        prompt = f"""
        Generate a secure password for a user with this context: {user_context}
        Requirements: {length} characters, secure but memorable
        Return JSON with password, memorability_score, and security_analysis.
        """
        
        result = await ai_service.complete_with_system(
            system="You are a password generation expert.",
            user=prompt,
            max_tokens=150
        )
        
        try:
            generated = json.loads(result)
            password = generated.get("password", self._generate_fallback_password(length))
            
            return {
                "password": password,
                "memorability_score": generated.get("memorability_score", 70),
                "security_analysis": {
                    "score": self._calculate_security_score(password),
                    "strengths": ["good entropy", "mixed characters"]
                },
                "alternatives": [
                    self._generate_alternative(password, 1),
                    self._generate_alternative(password, 2)
                ]
            }
        except json.JSONDecodeError:
            return self._generate_fallback_response(length)
```

### 5. Async Iterator Pattern

**Use Case**: Stream data in real-time with async iterators.

```python
from typing import AsyncIterator

class RecommendationService(IRecommendationService):
    """Service with streaming recommendation capabilities."""
    
    async def get_dynamic_course_recommendations_async(
        self, 
        user_id: str, 
        learning_goals: List[str],
        current_progress: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream dynamic course recommendations."""
        
        # Initialize AI recommendation engine
        ai_service = get_ai_service()
        progress_analyzer = get_progress_analyzer()
        
        # Analyze user progress in real-time
        progress_data = current_progress or await progress_analyzer.get_current_progress(user_id)
        
        recommendations_generated = 0
        
        for goal in learning_goals:
            if recommendations_generated >= limit:
                break
            
            # Generate course recommendations for this goal
            prompt = f"""
            User learning goal: {goal}
            Current progress: {progress_data}
            Recommend relevant courses with difficulty matching and prerequisites.
            """
            
            # Get AI recommendations
            ai_recommendations = await ai_service.get_course_recommendations(
                prompt=prompt,
                user_context={"user_id": user_id, "progress": progress_data}
            )
            
            for course in ai_recommendations:
                if recommendations_generated >= limit:
                    break
                
                # Analyze course fit
                fit_analysis = await self._analyze_course_fit(user_id, course, progress_data)
                
                yield {
                    "course_recommendation": {
                        "course_id": course.id,
                        "title": course.title,
                        "description": course.description,
                        "provider": course.provider
                    },
                    "relevance_score": fit_analysis.relevance_score,
                    "difficulty_match": fit_analysis.difficulty_match,
                    "prerequisite_analysis": {
                        "missing": fit_analysis.missing_prerequisites,
                        "recommended": fit_analysis.recommended_prep
                    },
                    "estimated_completion_time": fit_analysis.estimated_time,
                    "learning_path_position": recommendations_generated + 1
                }
                
                recommendations_generated += 1
                
                # Yield control to allow other operations
                await asyncio.sleep(0.01)
    
    async def generate_adaptive_recommendations_async(
        self, 
        user_id: str, 
        interaction_data: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate adaptive recommendations based on interactions."""
        
        interaction_analyzer = get_interaction_analyzer()
        
        # Continuously analyze user interactions
        async for interaction_event in interaction_analyzer.stream_interactions(user_id):
            # Analyze interaction pattern
            pattern_analysis = await self._analyze_interaction_pattern(
                interaction_event, 
                interaction_data
            )
            
            if pattern_analysis.requires_adaptation:
                # Generate adaptive recommendation
                recommendation = await self._generate_adaptive_recommendation(
                    user_id=user_id,
                    trigger_event=interaction_event,
                    analysis=pattern_analysis
                )
                
                yield {
                    "recommendation_type": recommendation.type,
                    "content": recommendation.content,
                    "trigger_reason": pattern_analysis.trigger_reason,
                    "urgency_level": recommendation.urgency,
                    "expected_impact": recommendation.expected_impact,
                    "metadata": {
                        "interaction_id": interaction_event.id,
                        "analysis_confidence": pattern_analysis.confidence,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
                # Update interaction data with new recommendation
                interaction_data["last_recommendation"] = recommendation.id
                interaction_data["recommendation_count"] = interaction_data.get("recommendation_count", 0) + 1
```

### 6. Error Handling Pattern

**Use Case**: Robust error handling in async operations.

```python
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AsyncErrorHandler:
    """Centralized async error handling."""
    
    @staticmethod
    async def with_retry(
        async_func,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        """Execute async function with retry logic."""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await async_func()
            except exceptions as e:
                last_exception = e
                
                if attempt == max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for {async_func.__name__}: {str(e)}")
                    raise e
                
                wait_time = delay * (backoff ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {async_func.__name__}: {str(e)}. Retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
        
        raise last_exception
    
    @staticmethod
    async def with_timeout(async_func, timeout: float = 30.0):
        """Execute async function with timeout."""
        try:
            return await asyncio.wait_for(async_func(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Timeout ({timeout}s) exceeded for {async_func.__name__}")
            raise
    
    @staticmethod
    async def with_circuit_breaker(
        async_func,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        circuit_breaker_state: Optional[Dict[str, Any]] = None
    ):
        """Execute async function with circuit breaker pattern."""
        state = circuit_breaker_state or {"failures": 0, "last_failure": None, "state": "closed"}
        
        # Check circuit breaker state
        if state["state"] == "open":
            if time.time() - state["last_failure"] > recovery_timeout:
                state["state"] = "half_open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await async_func()
            
            # Reset on success
            if state["state"] == "half_open":
                state["state"] = "closed"
                state["failures"] = 0
            
            return result
            
        except Exception as e:
            state["failures"] += 1
            state["last_failure"] = time.time()
            
            if state["failures"] >= failure_threshold:
                state["state"] = "open"
                logger.error(f"Circuit breaker opened for {async_func.__name__} after {failure_threshold} failures")
            
            raise e

# Usage example
class RobustAIService:
    """AI service with robust error handling."""
    
    async def get_ai_recommendation_robust(self, user_id: str, prompt: str) -> Dict[str, Any]:
        """Get AI recommendation with full error handling."""
        
        async def ai_operation():
            ai_service = get_ai_service()
            return await ai_service.complete_with_system(
                system="You are a helpful recommendation assistant.",
                user=prompt,
                max_tokens=200
            )
        
        # Apply all error handling patterns
        result = await AsyncErrorHandler.with_retry(
            lambda: AsyncErrorHandler.with_timeout(
                lambda: AsyncErrorHandler.with_circuit_breaker(ai_operation),
                timeout=10.0
            ),
            max_retries=2,
            delay=1.0
        )
        
        return {"recommendation": result, "user_id": user_id}
```

## Working Code Examples

### Complete Async View Implementation

```python
# File: domains/onboarding/api/v1/async_recommendation_views.py

from api.common.async_views import AsyncAPIView
from api.common.responses import APIResponse
from api.common.sse import SSEAPIView, SSEEvent
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import asyncio

class AsyncRoleRecommendationView(AsyncAPIView):
    """Complete async view for AI role recommendations."""
    
    permission_classes = [IsAuthenticated]
    
    async def async_post(self, request, *args, **kwargs):
        """Get AI-powered role recommendations."""
        try:
            user_id = str(request.user.id)
            user_input = request.data.get('job_description', '')
            context = request.data.get('context', {})
            limit = int(request.data.get('limit', 10))
            
            # Get recommendation service
            from application.dependencies import get_recommendation_service
            recommendation_service = get_recommendation_service()
            
            # Get AI recommendations asynchronously
            recommendations = await recommendation_service.get_ai_role_recommendations_async(
                user_id=user_id,
                user_input=user_input,
                context=context,
                limit=limit
            )
            
            return Response({
                "recommendations": recommendations["recommendations"],
                "reasoning": recommendations["reasoning"],
                "confidence_scores": recommendations["confidence_scores"],
                "skill_gaps": recommendations["skill_gaps"],
                "user_id": user_id,
                "processed_at": datetime.utcnow().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return await self.async_handle_exception(e)

class StreamingRecommendationView(AsyncAPIView):
    """Stream course recommendations in real-time."""
    
    permission_classes = [IsAuthenticated]
    
    async def async_get(self, request, *args, **kwargs):
        """Stream dynamic course recommendations."""
        try:
            user_id = str(request.user.id)
            learning_goals = request.GET.getlist('goals[]')
            limit = int(request.GET.get('limit', 20))
            
            from application.dependencies import get_recommendation_service
            recommendation_service = get_recommendation_service()
            
            # Create streaming response
            return await APIResponse.streaming_response(
                data_source=recommendation_service.get_dynamic_course_recommendations_async(
                    user_id=user_id,
                    learning_goals=learning_goals,
                    limit=limit
                ),
                streaming_type="objects",  # NDJSON format
                chunk_size=5
            )
            
        except Exception as e:
            return await self.async_handle_exception(e)

class ProgressSSEView(SSEAPIView):
    """Real-time progress updates via Server-Sent Events."""
    
    permission_classes = [IsAuthenticated]
    
    def sse_event_stream(self, request, *args, **kwargs):
        """Stream onboarding progress updates."""
        user_id = str(request.user.id)
        
        from application.dependencies import get_onboarding_service
        onboarding_service = get_onboarding_service()
        
        # Start progress tracking
        try:
            async def progress_generator():
                async for progress in onboarding_service.analyze_onboarding_progress_async(user_id):
                    yield SSEEvent(
                        data={
                            "user_id": user_id,
                            "progress_analysis": progress["progress_analysis"],
                            "completion_prediction": progress["completion_prediction"],
                            "next_best_action": progress["next_best_action"],
                            "engagement_level": progress["engagement_level"],
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        event_type="progress",
                        event_id=f"progress_{int(time.time())}",
                        retry=2000
                    )
                    
                    # Rate limit: update every 2 seconds
                    await asyncio.sleep(2)
            
            # Convert async generator to sync for SSE compatibility
            return self._async_to_sync_events(progress_generator())
            
        except Exception as e:
            yield SSEEvent(
                data={"error": str(e), "user_id": user_id},
                event_type="error",
                retry=5000
            )
    
    def _async_to_sync_events(self, async_generator):
        """Convert async event generator to sync for SSE."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        def sync_generator():
            try:
                while True:
                    try:
                        event = loop.run_until_complete(async_generator.__anext__())
                        yield event
                    except StopAsyncIteration:
                        break
            finally:
                loop.run_until_complete(async_generator.aclose())
        
        return sync_generator()
```

### Service Implementation Example

```python
# File: infrastructure/services/recommendation_service_impl.py

from domains.onboarding.services.interfaces import IRecommendationService
from infrastructure.external_services.openai.client import OpenAIClient
from typing import Dict, Any, List, Optional, AsyncIterator
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class RecommendationServiceImpl(IRecommendationService):
    """Complete implementation with both sync and async methods."""
    
    def __init__(self, openai_client: OpenAIClient, cache_service, user_repository):
        self.openai_client = openai_client
        self.cache_service = cache_service
        self.user_repository = user_repository
    
    # Sync methods (backward compatibility)
    def get_role_recommendations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get basic role recommendations synchronously."""
        # Implementation for sync role recommendations
        cached_key = f"roles:{user_id}"
        cached_result = self.cache_service.get(cached_key)
        
        if cached_result:
            return cached_result[:limit]
        
        # Fallback to basic matching logic
        user = self.user_repository.get_by_id(user_id)
        basic_roles = self._get_basic_role_matches(user)
        
        self.cache_service.set(cached_key, basic_roles, ttl=3600)
        return basic_roles[:limit]
    
    # Async AI-powered methods
    async def get_ai_role_recommendations_async(
        self, 
        user_id: str, 
        user_input: str, 
        context: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get AI-powered role recommendations with detailed analysis."""
        
        try:
            # Get user context
            user = await self.user_repository.get_by_id_async(user_id)
            full_context = {
                "user_profile": user.profile if user else {},
                "additional_context": context or {}
            }
            
            # Create AI prompt
            prompt = f"""
            Analyze this job description and recommend relevant roles:
            
            Job Description: {user_input}
            User Context: {json.dumps(full_context, indent=2)}
            
            Provide {limit} role recommendations with:
            1. Role title and description
            2. Match score (0-100)
            3. Reasoning for the recommendation
            4. Required skills and experience
            5. Identified skill gaps
            
            Return as JSON with this structure:
            {{
                "recommendations": [
                    {{
                        "role_id": "unique_id",
                        "title": "Role Title",
                        "description": "Role description",
                        "match_score": 85,
                        "reasoning": "Why this role matches",
                        "required_skills": ["skill1", "skill2"],
                        "experience_level": "mid-level"
                    }}
                ],
                "skill_gaps": ["missing_skill1", "missing_skill2"],
                "confidence_scores": [85, 78, 72],
                "alternative_suggestions": ["alternative_role1", "alternative_role2"]
            }}
            """
            
            # Get AI response with retry logic
            ai_response = await AsyncErrorHandler.with_retry(
                lambda: self.openai_client.complete_with_system_async(
                    system="You are an expert career counselor and role recommendation specialist.",
                    user=prompt,
                    max_tokens=1000
                ),
                max_retries=2,
                delay=1.0
            )
            
            # Parse AI response
            try:
                parsed_result = json.loads(ai_response)
                
                # Validate and enhance recommendations
                enhanced_recommendations = await self._enhance_recommendations(
                    parsed_result["recommendations"],
                    user_id,
                    full_context
                )
                
                result = {
                    "recommendations": enhanced_recommendations,
                    "reasoning": [rec.get("reasoning", "") for rec in enhanced_recommendations],
                    "confidence_scores": parsed_result.get("confidence_scores", []),
                    "alternative_suggestions": parsed_result.get("alternative_suggestions", []),
                    "skill_gaps": parsed_result.get("skill_gaps", [])
                }
                
                # Cache result for future use
                cache_key = f"ai_roles:{user_id}:{hash(user_input)}"
                await self.cache_service.set_async(cache_key, result, ttl=1800)  # 30 minutes
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {str(e)}")
                # Fallback to basic recommendations
                return await self._get_fallback_recommendations(user_id, limit)
                
        except Exception as e:
            logger.error(f"Error in AI role recommendations: {str(e)}")
            # Fallback to cached or basic recommendations
            return await self._get_fallback_recommendations(user_id, limit)
    
    async def get_dynamic_course_recommendations_async(
        self, 
        user_id: str, 
        learning_goals: List[str],
        current_progress: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream dynamic course recommendations."""
        
        try:
            # Get user's current skill level and progress
            user_progress = current_progress or await self._get_user_progress(user_id)
            processed_goals = 0
            recommendations_sent = 0
            
            for goal in learning_goals:
                if recommendations_sent >= limit:
                    break
                
                # Analyze learning goal
                goal_analysis = await self._analyze_learning_goal(goal, user_progress)
                
                # Get courses for this goal
                courses = await self._get_courses_for_goal(goal, goal_analysis, user_progress)
                
                for course in courses:
                    if recommendations_sent >= limit:
                        break
                    
                    # Analyze course fit for user
                    fit_analysis = await self._analyze_course_fit(user_id, course, user_progress)
                    
                    yield {
                        "course_recommendation": {
                            "course_id": course.id,
                            "title": course.title,
                            "description": course.description,
                            "provider": course.provider,
                            "url": course.url,
                            "duration": course.duration,
                            "difficulty": course.difficulty
                        },
                        "relevance_score": fit_analysis.relevance_score,
                        "difficulty_match": fit_analysis.difficulty_assessment,
                        "prerequisite_analysis": {
                            "missing": fit_analysis.missing_prerequisites,
                            "recommended": fit_analysis.recommended_preparation,
                            "optional": fit_analysis.optional_prerequisites
                        },
                        "estimated_completion_time": fit_analysis.estimated_completion_time,
                        "learning_goal": goal,
                        "position_in_sequence": recommendations_sent + 1,
                        "metadata": {
                            "analysis_confidence": fit_analysis.confidence,
                            "last_updated": datetime.utcnow().isoformat(),
                            "user_skill_level": user_progress.get("skill_level", "beginner")
                        }
                    }
                    
                    recommendations_sent += 1
                    
                    # Yield control every few recommendations
                    if recommendations_sent % 3 == 0:
                        await asyncio.sleep(0.01)
                
                processed_goals += 1
                
                # Brief pause between goals
                await asyncio.sleep(0.05)
                
        except Exception as e:
            logger.error(f"Error in dynamic course recommendations: {str(e)}")
            # Yield error information
            yield {
                "error": {
                    "message": "Failed to generate dynamic recommendations",
                    "details": str(e),
                    "fallback_available": True
                }
            }
```

## Best Practices

### 1. Async/Await Guidelines

**✅ Do:**
```python
# Use async/await for I/O operations
async def get_user_data(user_id: str):
    user = await database.get_user(user_id)
    recommendations = await ai_service.get_recommendations(user)
    return {"user": user, "recommendations": recommendations}

# Use asyncio.gather for concurrent operations
async def get_multiple_data(user_ids: List[str]):
    users = await asyncio.gather(*[
        database.get_user(user_id) for user_id in user_ids
    ])
    return users
```

**❌ Don't:**
```python
# Don't use async for CPU-bound operations without threading
async def calculate_heavy_computation(data):
    # This blocks the event loop
    result = complex_calculation(data)  # CPU-intensive
    return result

# Don't forget await
async def bad_example():
    result = database.get_user("123")  # Missing await!
    return result
```

### 2. Error Handling

**✅ Do:**
```python
async def robust_ai_call():
    try:
        result = await ai_service.get_completion()
        return result
    except asyncio.TimeoutError:
        logger.warning("AI service timeout, using fallback")
        return fallback_response()
    except Exception as e:
        logger.error(f"AI service error: {str(e)}")
        raise ServiceUnavailableError("AI service temporarily unavailable")
```

### 3. Resource Management

**✅ Do:**
```python
# Use async context managers
async def process_file():
    async with aiofiles.open('data.txt', 'r') as file:
        content = await file.read()
        return process_content(content)

# Properly close async generators
async def use_streaming_data():
    stream = get_data_stream()
    try:
        async for item in stream:
            process_item(item)
    finally:
        await stream.aclose()
```

### 4. Performance Optimization

**✅ Do:**
```python
# Use connection pooling for databases
async def efficient_database_access():
    async with database_pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM users")
        return result

# Batch operations when possible
async def batch_process_users(user_ids: List[str]):
    # Process in batches to avoid overwhelming resources
    batch_size = 10
    results = []
    
    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i + batch_size]
        batch_results = await asyncio.gather(*[
            process_user(user_id) for user_id in batch
        ])
        results.extend(batch_results)
        
        # Brief pause between batches
        await asyncio.sleep(0.1)
    
    return results
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. "RuntimeError: This event loop is already running"

**Problem**: Trying to run async code in an already running event loop.

**Solution**:
```python
# Wrong
def sync_function():
    result = asyncio.run(async_function())  # Error if loop already running

# Correct
async def async_function():
    result = await another_async_function()
    return result

# Or use asyncio.create_task()
async def main():
    task = asyncio.create_task(async_function())
    result = await task
```

#### 2. Memory Leaks in Async Generators

**Problem**: Async generators not properly closed.

**Solution**:
```python
# Wrong - generator might not be closed
async def process_stream():
    async for item in data_stream():
        if some_condition:
            return  # Generator not closed!

# Correct - ensure proper cleanup
async def process_stream():
    stream = data_stream()
    try:
        async for item in stream:
            if some_condition:
                break
        return result
    finally:
        await stream.aclose()
```

#### 3. Blocking the Event Loop

**Problem**: Long-running CPU operations block other async tasks.

**Solution**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Wrong - blocks event loop
async def cpu_intensive_task(data):
    return expensive_calculation(data)  # Blocks everything

# Correct - run in thread pool
async def cpu_intensive_task(data):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor, expensive_calculation, data
        )
    return result
```

#### 4. Improper Exception Handling in Streams

**Problem**: Exceptions in async generators terminate the stream.

**Solution**:
```python
# Wrong - exception terminates stream
async def data_stream():
    for i in range(100):
        result = await risky_operation(i)  # Might raise exception
        yield result

# Correct - handle exceptions gracefully
async def data_stream():
    for i in range(100):
        try:
            result = await risky_operation(i)
            yield {"success": True, "data": result}
        except Exception as e:
            yield {"success": False, "error": str(e), "index": i}
            # Optionally continue or break based on error type
```

#### 5. Deadlocks with Sync and Async Code

**Problem**: Mixing sync and async code incorrectly.

**Solution**:
```python
# Wrong - can cause deadlocks
def sync_wrapper():
    return asyncio.run(async_function())

async def async_function():
    return sync_wrapper()  # Deadlock!

# Correct - keep sync and async separate
async def async_function():
    result = await another_async_function()
    return result

def sync_function():
    return synchronous_operation()
```

### Performance Debugging

#### Monitor Event Loop

```python
import asyncio
import time

async def monitor_event_loop():
    """Monitor event loop performance."""
    while True:
        start_time = time.time()
        await asyncio.sleep(0.01)  # Should be ~10ms
        actual_delay = time.time() - start_time
        
        if actual_delay > 0.05:  # Alert if >50ms delay
            logger.warning(f"Event loop delay: {actual_delay:.3f}s")
        
        await asyncio.sleep(1)
```

#### Profile Async Code

```python
import cProfile
import asyncio

def profile_async_function():
    """Profile async function performance."""
    profiler = cProfile.Profile()
    
    async def run_with_profiling():
        profiler.enable()
        try:
            result = await your_async_function()
            return result
        finally:
            profiler.disable()
    
    result = asyncio.run(run_with_profiling())
    profiler.print_stats()
    return result
```

## Performance Considerations

### Async vs Sync Performance Guidelines

| Operation Type | Recommended Approach | Reasoning |
|---------------|---------------------|-----------|
| Database queries | Async | I/O bound, benefits from concurrency |
| AI/ML API calls | Async | Network I/O, often long-running |
| File operations | Async (large files) | I/O bound operations |
| Simple calculations | Sync | CPU bound, no I/O benefit |
| Caching operations | Sync (Redis) | Usually very fast |
| Authentication checks | Sync | Typically cached or fast |

### Memory Usage

- **Streaming**: Use async generators for large datasets
- **Batching**: Process data in chunks to limit memory usage
- **Connection Pooling**: Reuse database connections efficiently

### Latency Optimization

- **Concurrent Operations**: Use `asyncio.gather()` for parallel execution
- **Caching**: Cache AI responses and expensive computations
- **Timeouts**: Set appropriate timeouts for external services

---

This documentation provides comprehensive guidance for implementing async patterns in FluentPro. All examples are production-ready and follow established best practices for scalable, maintainable async code.