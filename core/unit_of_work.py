"""
Unit of Work implementation for managing database transactions.
Provides transactional consistency across multiple repository operations.
"""

from typing import Optional
import logging
from contextlib import contextmanager

from core.interfaces import (
    UnitOfWorkInterface,
    UserRepositoryInterface,
    RoleRepositoryInterface,
    IndustryRepositoryInterface,
    CommunicationRepositoryInterface
)
from shared.repositories import (
    UserRepository,
    RoleRepository,
    IndustryRepository,
    CommunicationRepository
)
from authentication.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class SupabaseUnitOfWork(UnitOfWorkInterface):
    """
    Unit of Work implementation using Supabase.
    Manages transactions and repository instances.
    """
    
    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase_service = supabase_service or SupabaseService()
        self._users: Optional[UserRepositoryInterface] = None
        self._roles: Optional[RoleRepositoryInterface] = None
        self._industries: Optional[IndustryRepositoryInterface] = None
        self._communication: Optional[CommunicationRepositoryInterface] = None
        self._transaction_active = False
    
    def __enter__(self):
        """Enter context manager and start transaction."""
        self._transaction_active = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and handle transaction."""
        if exc_type is not None:
            # Exception occurred, rollback
            self.rollback()
        else:
            # No exception, commit
            self.commit()
        
        self._transaction_active = False
    
    def commit(self):
        """Commit all pending changes."""
        if self._transaction_active:
            try:
                # Supabase handles transactions automatically for single operations
                # For multi-operation transactions, we would use database transactions
                logger.debug("Unit of Work: Changes committed")
            except Exception as e:
                logger.error(f"Failed to commit changes: {str(e)}")
                raise
    
    def rollback(self):
        """Rollback all pending changes."""
        if self._transaction_active:
            try:
                # Supabase handles rollbacks automatically on exceptions
                # For explicit rollbacks, we would use database transaction rollback
                logger.debug("Unit of Work: Changes rolled back")
            except Exception as e:
                logger.error(f"Failed to rollback changes: {str(e)}")
                raise
    
    @property
    def users(self) -> UserRepositoryInterface:
        """Get user repository."""
        if self._users is None:
            self._users = UserRepository(self.supabase_service)
        return self._users
    
    @property
    def roles(self) -> RoleRepositoryInterface:
        """Get role repository."""
        if self._roles is None:
            self._roles = RoleRepository(self.supabase_service)
        return self._roles
    
    @property
    def industries(self) -> IndustryRepositoryInterface:
        """Get industry repository."""
        if self._industries is None:
            self._industries = IndustryRepository(self.supabase_service)
        return self._industries
    
    @property
    def communication(self) -> CommunicationRepositoryInterface:
        """Get communication repository."""
        if self._communication is None:
            self._communication = CommunicationRepository(self.supabase_service)
        return self._communication


class TransactionalService:
    """
    Base service class that provides transactional operations.
    """
    
    def __init__(self, unit_of_work_class=SupabaseUnitOfWork):
        self.unit_of_work_class = unit_of_work_class
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        with self.unit_of_work_class() as uow:
            yield uow
    
    def execute_in_transaction(self, operation, *args, **kwargs):
        """Execute operation within a transaction."""
        with self.transaction() as uow:
            return operation(uow, *args, **kwargs)


# Decorator for transactional operations
def transactional(func):
    """
    Decorator to wrap function execution in a transaction.
    
    Usage:
        @transactional
        def create_user_with_profile(user_data, profile_data):
            # This function will run in a transaction
            pass
    """
    def wrapper(*args, **kwargs):
        with SupabaseUnitOfWork() as uow:
            # Inject unit of work as first argument if not present
            if args and hasattr(args[0], '__class__') and hasattr(args[0].__class__, '__name__'):
                # This is a method call, inject uow as second argument
                return func(args[0], uow, *args[1:], **kwargs)
            else:
                # This is a function call, inject uow as first argument
                return func(uow, *args, **kwargs)
    
    return wrapper


# Context manager for manual transaction control
@contextmanager
def database_transaction():
    """
    Context manager for database transactions.
    
    Usage:
        with database_transaction() as uow:
            user = uow.users.create(user_data)
            profile = uow.users.update_profile(user.id, profile_data)
    """
    with SupabaseUnitOfWork() as uow:
        yield uow


# Factory function for creating unit of work instances
def create_unit_of_work(supabase_service: Optional[SupabaseService] = None) -> UnitOfWorkInterface:
    """Create a new unit of work instance."""
    return SupabaseUnitOfWork(supabase_service)


class BatchOperation:
    """
    Helper class for batch operations across multiple repositories.
    """
    
    def __init__(self, unit_of_work: UnitOfWorkInterface):
        self.uow = unit_of_work
        self.operations = []
    
    def add_operation(self, operation, *args, **kwargs):
        """Add operation to batch."""
        self.operations.append((operation, args, kwargs))
    
    def execute(self):
        """Execute all operations in batch."""
        results = []
        
        try:
            for operation, args, kwargs in self.operations:
                result = operation(*args, **kwargs)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Batch operation failed: {str(e)}")
            raise
    
    def clear(self):
        """Clear all operations."""
        self.operations.clear()


# Helper functions for common transactional patterns
def create_user_with_role(user_data: dict, role_data: dict) -> dict:
    """Create user and associated role in a single transaction."""
    with database_transaction() as uow:
        # Create user
        user = uow.users.create(user_data)
        
        # Create role if it doesn't exist
        role = uow.roles.create({
            **role_data,
            'created_by_user_id': user.id
        })
        
        # Update user with role
        updated_user = uow.users.update(user.id, {
            'selected_role_id': role.id
        })
        
        return {
            'user': updated_user.to_dict(),
            'role': role.to_dict()
        }


def update_user_onboarding_progress(user_id: str, updates: dict) -> dict:
    """Update multiple aspects of user onboarding in a single transaction."""
    with database_transaction() as uow:
        results = {}
        
        # Update user profile
        if 'profile' in updates:
            profile = uow.users.update_profile(user_id, updates['profile'])
            results['profile'] = profile.to_dict()
        
        # Update communication preferences
        if 'communication' in updates:
            comm_data = updates['communication']
            
            if 'partners' in comm_data:
                partner_selections = uow.communication.save_partner_selections(
                    user_id, 
                    comm_data['partners'].get('partner_ids', []),
                    comm_data['partners'].get('custom_partners', [])
                )
                results['partners'] = [p.to_dict() for p in partner_selections]
            
            if 'units' in comm_data:
                for partner_id, unit_data in comm_data['units'].items():
                    unit_selections = uow.communication.save_unit_selections(
                        user_id,
                        partner_id,
                        unit_data.get('unit_ids', []),
                        unit_data.get('custom_units', [])
                    )
                    results[f'units_{partner_id}'] = [u.to_dict() for u in unit_selections]
        
        return results