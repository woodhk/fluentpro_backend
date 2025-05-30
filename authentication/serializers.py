from rest_framework import serializers
from datetime import datetime, date
import re


class SignUpSerializer(serializers.Serializer):
    """
    Serializer for user sign up
    """
    full_name = serializers.CharField(
        max_length=50,
        min_length=2,
        help_text="Full name between 2-50 characters"
    )
    email = serializers.EmailField(
        help_text="Valid email address"
    )
    password = serializers.CharField(
        min_length=8,
        help_text="Password with minimum 8 characters, uppercase, lowercase, number, and special character"
    )
    date_of_birth = serializers.DateField(
        help_text="Date of birth (user must be at least 13 years old)"
    )
    
    def validate_full_name(self, value):
        """
        Validate full name contains only letters and spaces
        """
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError("Full name can only contain letters and spaces")
        return value.strip()
    
    def validate_password(self, value):
        """
        Validate password complexity
        """
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain at least one number")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character")
        return value
    
    def validate_date_of_birth(self, value):
        """
        Validate user is at least 13 years old
        """
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if age < 13:
            raise serializers.ValidationError("User must be at least 13 years old")
        
        return value


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField(
        help_text="User's email address"
    )
    password = serializers.CharField(
        help_text="User's password"
    )


class AuthResponseSerializer(serializers.Serializer):
    """
    Serializer for authentication response
    """
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default="Bearer")
    expires_in = serializers.IntegerField()
    user = serializers.DictField()


class UserSerializer(serializers.Serializer):
    """
    Serializer for user data
    """
    id = serializers.CharField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    date_of_birth = serializers.DateField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    """
    Serializer for refresh token request
    """
    refresh_token = serializers.CharField(
        help_text="Refresh token to get new access token"
    )


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for logout request
    """
    refresh_token = serializers.CharField(
        help_text="Refresh token to revoke"
    )


class Auth0CallbackSerializer(serializers.Serializer):
    """
    Serializer for Auth0 callback data
    """
    code = serializers.CharField(
        help_text="Authorization code from Auth0"
    )
    state = serializers.CharField(
        required=False,
        help_text="State parameter for CSRF protection"
    )