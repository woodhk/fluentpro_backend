from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from datetime import datetime


class UserManager(BaseUserManager):
    """
    Custom user manager for Fluentpro users
    """
    def create_user(self, email, full_name, date_of_birth, password=None, auth0_id=None):
        if not email:
            raise ValueError('Users must have an email address')
        
        user = self.model(
            email=self.normalize_email(email),
            full_name=full_name,
            date_of_birth=date_of_birth,
            auth0_id=auth0_id
        )
        
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, full_name, date_of_birth, password=None):
        user = self.create_user(
            email=email,
            full_name=full_name,
            date_of_birth=date_of_birth,
            password=password
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """
    Custom user model that matches the iOS app requirements
    """
    # Fields matching the iOS app
    id = models.CharField(max_length=255, primary_key=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    date_of_birth = models.DateField()
    
    # Auth0 integration
    auth0_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    
    # Django specific fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For JWT authentication - we don't need to store password
    password = models.CharField(max_length=128, null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'date_of_birth']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        return True
    
    def has_module_perms(self, app_label):
        return True
    
    @property
    def is_authenticated(self):
        return True
    
    def save(self, *args, **kwargs):
        if not self.id:
            # Generate a unique ID if not provided
            import uuid
            self.id = str(uuid.uuid4())
        super().save(*args, **kwargs)


# Simple user object for JWT authentication without database
class SimpleUser:
    """
    A simple user object for JWT authentication that doesn't require database storage
    """
    def __init__(self, auth0_id, email, is_authenticated=True):
        self.auth0_id = auth0_id
        self.email = email
        self.is_authenticated = is_authenticated
        self.is_active = True
        self.is_anonymous = False
    
    def __str__(self):
        return self.email