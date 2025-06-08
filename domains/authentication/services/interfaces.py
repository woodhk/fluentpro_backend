"""
Authentication Domain Service Interfaces

Defines contracts for authentication-related business services.
These interfaces abstract the business logic from implementation details.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime


class IAuthenticationService(ABC):
    """External authentication service interface"""
    
    @abstractmethod
    async def create_user(self, email: str, password: str, metadata: Dict[str, Any]) -> str:
        """Create user in external auth system, return auth_id"""
        pass
    
    @abstractmethod
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return claims"""
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke a token"""
        pass


class ITokenService(ABC):
    """JWT token generation service"""
    
    @abstractmethod
    async def create_access_token(self, user_id: str, claims: Dict[str, Any]) -> str:
        """Create access token"""
        pass
    
    @abstractmethod
    async def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token"""
        pass


class IPasswordService(ABC):
    """
    Password management service interface.
    
    Handles password hashing, validation, and security policies.
    Includes both synchronous and asynchronous methods for AI-powered security analysis.
    """
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """
        Hash a password using secure algorithm.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        pass
    
    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches
        """
        pass
    
    @abstractmethod
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password meets security requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Dict containing:
                - is_valid: Whether password meets requirements
                - errors: List of validation errors
                - score: Password strength score (0-100)
        """
        pass
    
    @abstractmethod
    def generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Password length
            
        Returns:
            Generated password
        """
        pass
    
    @abstractmethod
    def check_password_history(self, user_id: str, password: str) -> bool:
        """
        Check if password was previously used.
        
        Args:
            user_id: User's ID
            password: Password to check
            
        Returns:
            True if password was used before
        """
        pass
    
    # Async AI-powered methods for enhanced security analysis
    
    @abstractmethod
    async def analyze_password_security_async(self, password: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform AI-powered comprehensive password security analysis.
        
        Uses ML models to analyze password patterns, common attack vectors,
        and contextual security risks.
        
        Args:
            password: Password to analyze
            context: Optional context (user info, previous passwords, etc.)
            
        Returns:
            Dict containing:
                - security_score: AI-calculated security score (0-100)
                - vulnerability_analysis: List of detected vulnerabilities
                - recommendations: AI-generated security recommendations
                - attack_resistance: Resistance against different attack types
                - entropy_analysis: Password entropy and randomness analysis
        """
        pass
    
    @abstractmethod
    async def detect_password_patterns_async(self, password: str) -> Dict[str, Any]:
        """
        Detect password patterns using AI pattern recognition.
        
        Args:
            password: Password to analyze
            
        Returns:
            Dict containing:
                - detected_patterns: List of detected patterns
                - pattern_strength: Strength of each pattern
                - predictability_score: How predictable the password is
                - suggestions: AI-generated improvement suggestions
        """
        pass
    
    @abstractmethod
    async def generate_contextual_password_async(self, user_context: Dict[str, Any], length: int = 16) -> Dict[str, Any]:
        """
        Generate AI-optimized password based on user context.
        
        Args:
            user_context: User context for generating secure but memorable password
            length: Desired password length
            
        Returns:
            Dict containing:
                - password: Generated password
                - memorability_score: How memorable the password is
                - security_analysis: Security analysis of generated password
                - alternatives: Alternative password suggestions
        """
        pass
    
    @abstractmethod
    async def predict_password_compromise_risk_async(self, user_id: str, password: str) -> Dict[str, Any]:
        """
        Predict password compromise risk using AI analysis.
        
        Args:
            user_id: User's ID for context
            password: Password to analyze
            
        Returns:
            Dict containing:
                - risk_score: Compromise risk score (0-100)
                - risk_factors: Identified risk factors
                - breach_probability: Probability of being in future breaches
                - recommended_actions: AI-recommended security actions
        """
        pass


class ISessionService(ABC):
    """
    Session management service interface.
    
    Handles user session lifecycle and management.
    Includes both synchronous and asynchronous methods for AI-powered session analysis.
    """
    
    @abstractmethod
    def create_session(self, user_id: str, device_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new user session.
        
        Args:
            user_id: User's ID
            device_info: Optional device/browser information
            
        Returns:
            Session ID
        """
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data if found
        """
        pass
    
    @abstractmethod
    def update_session_activity(self, session_id: str) -> bool:
        """
        Update session last activity timestamp.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if update successful
        """
        pass
    
    @abstractmethod
    def end_session(self, session_id: str) -> bool:
        """
        End a user session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session ended
        """
        pass
    
    @abstractmethod
    def get_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            List of active sessions
        """
        pass
    
    @abstractmethod
    def end_all_sessions(self, user_id: str, except_current: Optional[str] = None) -> int:
        """
        End all sessions for a user.
        
        Args:
            user_id: User's ID
            except_current: Optional session ID to keep active
            
        Returns:
            Number of sessions ended
        """
        pass
    
    # Async AI-powered methods for session analysis and security
    
    @abstractmethod
    async def analyze_session_anomalies_async(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Perform AI-powered session anomaly detection.
        
        Analyzes session patterns, device fingerprints, and behavior patterns
        to detect potential security threats or unusual activity.
        
        Args:
            user_id: User's ID
            session_id: Session ID to analyze
            
        Returns:
            Dict containing:
                - anomaly_score: AI-calculated anomaly score (0-100)
                - detected_anomalies: List of detected anomalies
                - risk_level: Risk level (low, medium, high, critical)
                - recommended_actions: AI-recommended security actions
                - behavior_analysis: Analysis of user behavior patterns
        """
        pass
    
    @abstractmethod
    async def predict_session_security_risk_async(self, user_id: str, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict security risk for a new session using AI analysis.
        
        Args:
            user_id: User's ID
            device_info: Device and browser information
            
        Returns:
            Dict containing:
                - risk_score: Predicted risk score (0-100)
                - risk_factors: Identified risk factors
                - device_trust_score: Device trustworthiness score
                - location_analysis: Location-based risk analysis
                - recommendations: Security recommendations
        """
        pass
    
    @abstractmethod
    async def analyze_user_session_patterns_async(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze user's session patterns using AI to establish behavioral baseline.
        
        Args:
            user_id: User's ID
            days: Number of days to analyze
            
        Returns:
            Dict containing:
                - typical_patterns: User's typical session patterns
                - peak_activity_times: Times when user is most active
                - device_preferences: Preferred devices and locations
                - behavior_baseline: Established behavioral baseline
                - pattern_confidence: Confidence in pattern analysis
        """
        pass
    
    @abstractmethod
    async def generate_session_insights_async(self, user_id: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate real-time session insights using AI analysis.
        
        Streams ongoing analysis of user sessions for real-time security monitoring.
        
        Args:
            user_id: User's ID
            
        Yields:
            Dict containing real-time session insights:
                - insight_type: Type of insight (security, behavior, performance)
                - message: Human-readable insight message
                - severity: Insight severity level
                - timestamp: When insight was generated
                - metadata: Additional insight data
        """
        yield {}  # Placeholder for async iterator
    
    @abstractmethod
    async def optimize_session_security_async(self, session_id: str) -> Dict[str, Any]:
        """
        Optimize session security settings using AI recommendations.
        
        Args:
            session_id: Session ID to optimize
            
        Returns:
            Dict containing:
                - optimizations_applied: List of applied optimizations
                - security_improvements: Security score improvements
                - performance_impact: Impact on session performance
                - recommendations: Additional recommendations
        """
        pass