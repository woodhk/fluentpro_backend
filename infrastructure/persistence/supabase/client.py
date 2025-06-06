"""
Supabase Client Interface

Defines the contract for Supabase database client implementation.
This interface abstracts Supabase-specific database operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime
from contextlib import contextmanager


class ISupabaseClient(ABC):
    """
    Supabase client interface for database operations.
    
    Provides access to Supabase's PostgreSQL database with
    real-time subscriptions and storage capabilities.
    """
    
    @abstractmethod
    def table(self, table_name: str) -> 'ISupabaseTable':
        """
        Get a table reference for operations.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table interface for chaining operations
        """
        pass
    
    @abstractmethod
    def rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Call a PostgreSQL function.
        
        Args:
            function_name: Name of the function
            params: Optional function parameters
            
        Returns:
            Function result
            
        Raises:
            SupabaseError: If function call fails
        """
        pass
    
    @abstractmethod
    @contextmanager
    def transaction(self):
        """
        Create a database transaction context.
        
        Usage:
            with client.transaction():
                # Perform multiple operations
                # All succeed or all fail
                
        Raises:
            SupabaseError: If transaction fails
        """
        pass
    
    @abstractmethod
    def auth(self) -> 'ISupabaseAuth':
        """
        Get auth client for authentication operations.
        
        Returns:
            Auth interface
        """
        pass
    
    @abstractmethod
    def storage(self) -> 'ISupabaseStorage':
        """
        Get storage client for file operations.
        
        Returns:
            Storage interface
        """
        pass
    
    @abstractmethod
    def realtime(self) -> 'ISupabaseRealtime':
        """
        Get realtime client for subscriptions.
        
        Returns:
            Realtime interface
        """
        pass


class ISupabaseTable(ABC):
    """
    Supabase table interface for query building and execution.
    
    Provides fluent interface for building and executing queries.
    """
    
    @abstractmethod
    def select(self, columns: str = "*") -> 'ISupabaseTable':
        """
        Select columns from table.
        
        Args:
            columns: Comma-separated column names or "*"
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def insert(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> 'ISupabaseTable':
        """
        Insert data into table.
        
        Args:
            data: Single record or list of records
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def update(self, data: Dict[str, Any]) -> 'ISupabaseTable':
        """
        Update records in table.
        
        Args:
            data: Fields to update
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def upsert(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> 'ISupabaseTable':
        """
        Insert or update records.
        
        Args:
            data: Single record or list of records
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def delete(self) -> 'ISupabaseTable':
        """
        Delete records from table.
        
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def eq(self, column: str, value: Any) -> 'ISupabaseTable':
        """
        Filter by equality.
        
        Args:
            column: Column name
            value: Value to match
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def neq(self, column: str, value: Any) -> 'ISupabaseTable':
        """
        Filter by inequality.
        
        Args:
            column: Column name
            value: Value to not match
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def gt(self, column: str, value: Any) -> 'ISupabaseTable':
        """
        Filter by greater than.
        
        Args:
            column: Column name
            value: Value to compare
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def gte(self, column: str, value: Any) -> 'ISupabaseTable':
        """
        Filter by greater than or equal.
        
        Args:
            column: Column name
            value: Value to compare
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def lt(self, column: str, value: Any) -> 'ISupabaseTable':
        """
        Filter by less than.
        
        Args:
            column: Column name
            value: Value to compare
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def lte(self, column: str, value: Any) -> 'ISupabaseTable':
        """
        Filter by less than or equal.
        
        Args:
            column: Column name
            value: Value to compare
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def in_(self, column: str, values: List[Any]) -> 'ISupabaseTable':
        """
        Filter by value in list.
        
        Args:
            column: Column name
            values: List of values
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def contains(self, column: str, value: Union[Dict, List]) -> 'ISupabaseTable':
        """
        Filter by array/jsonb contains.
        
        Args:
            column: Column name
            value: Value to check containment
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def order(self, column: str, desc: bool = False) -> 'ISupabaseTable':
        """
        Order results by column.
        
        Args:
            column: Column name
            desc: Whether to sort descending
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def limit(self, count: int) -> 'ISupabaseTable':
        """
        Limit number of results.
        
        Args:
            count: Maximum records to return
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def offset(self, count: int) -> 'ISupabaseTable':
        """
        Skip number of results.
        
        Args:
            count: Number of records to skip
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Execute the query.
        
        Returns:
            Query result with data and count
            
        Raises:
            SupabaseError: If query fails
        """
        pass


class ISupabaseAuth(ABC):
    """
    Supabase Auth interface for authentication operations.
    """
    
    @abstractmethod
    def sign_up(self, email: str, password: str, 
                options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sign up a new user.
        
        Args:
            email: User email
            password: User password
            options: Optional signup options
            
        Returns:
            User and session information
            
        Raises:
            SupabaseAuthError: If signup fails
        """
        pass
    
    @abstractmethod
    def sign_in_with_password(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User and session information
            
        Raises:
            SupabaseAuthError: If signin fails
        """
        pass
    
    @abstractmethod
    def sign_out(self) -> bool:
        """
        Sign out current user.
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current authenticated user.
        
        Returns:
            User information if authenticated
        """
        pass
    
    @abstractmethod
    def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh user session.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New session information
            
        Raises:
            SupabaseAuthError: If refresh fails
        """
        pass


class ISupabaseStorage(ABC):
    """
    Supabase Storage interface for file operations.
    """
    
    @abstractmethod
    def from_bucket(self, bucket_name: str) -> 'ISupabaseBucket':
        """
        Get bucket reference.
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            Bucket interface
        """
        pass
    
    @abstractmethod
    def create_bucket(self, bucket_name: str, 
                     options: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a new bucket.
        
        Args:
            bucket_name: Name for the bucket
            options: Optional bucket configuration
            
        Returns:
            True if created successfully
            
        Raises:
            SupabaseStorageError: If creation fails
        """
        pass
    
    @abstractmethod
    def delete_bucket(self, bucket_name: str) -> bool:
        """
        Delete a bucket.
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            True if deleted successfully
            
        Raises:
            SupabaseStorageError: If deletion fails
        """
        pass


class ISupabaseBucket(ABC):
    """
    Supabase bucket interface for file operations within a bucket.
    """
    
    @abstractmethod
    def upload(self, path: str, file_data: bytes, 
              file_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload a file to the bucket.
        
        Args:
            path: File path in bucket
            file_data: File content
            file_options: Optional file metadata
            
        Returns:
            Upload result with file info
            
        Raises:
            SupabaseStorageError: If upload fails
        """
        pass
    
    @abstractmethod
    def download(self, path: str) -> bytes:
        """
        Download a file from the bucket.
        
        Args:
            path: File path in bucket
            
        Returns:
            File content
            
        Raises:
            SupabaseStorageError: If download fails
        """
        pass
    
    @abstractmethod
    def delete(self, paths: List[str]) -> bool:
        """
        Delete files from the bucket.
        
        Args:
            paths: List of file paths
            
        Returns:
            True if all deleted successfully
            
        Raises:
            SupabaseStorageError: If deletion fails
        """
        pass
    
    @abstractmethod
    def get_public_url(self, path: str) -> str:
        """
        Get public URL for a file.
        
        Args:
            path: File path in bucket
            
        Returns:
            Public URL
        """
        pass


class ISupabaseRealtime(ABC):
    """
    Supabase Realtime interface for subscriptions.
    """
    
    @abstractmethod
    def channel(self, channel_name: str) -> 'ISupabaseChannel':
        """
        Create a realtime channel.
        
        Args:
            channel_name: Name for the channel
            
        Returns:
            Channel interface
        """
        pass


class ISupabaseChannel(ABC):
    """
    Supabase channel interface for realtime subscriptions.
    """
    
    @abstractmethod
    def on(self, event: str, filter: Optional[str] = None, 
           callback: Optional[callable] = None) -> 'ISupabaseChannel':
        """
        Subscribe to database changes.
        
        Args:
            event: Event type (INSERT, UPDATE, DELETE, *)
            filter: Optional filter expression
            callback: Function to call on event
            
        Returns:
            Self for chaining
        """
        pass
    
    @abstractmethod
    def subscribe(self) -> bool:
        """
        Start listening to subscribed events.
        
        Returns:
            True if subscription successful
        """
        pass
    
    @abstractmethod
    def unsubscribe(self) -> bool:
        """
        Stop listening to events.
        
        Returns:
            True if unsubscription successful
        """
        pass