"""
Test database management utilities.
Provides utilities for setting up, tearing down, and managing test databases.
"""

import os
import tempfile
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from django.db import connections, transaction
from django.core.management import call_command
from django.test.utils import setup_test_environment, teardown_test_environment
from django.conf import settings


class TestDatabaseManager:
    """
    Manages test database lifecycle including setup, cleanup, and isolation.
    """
    
    def __init__(self):
        self.temp_db_files: List[str] = []
        self.original_databases: Optional[Dict[str, Any]] = None
    
    def setup_test_database(self, db_alias: str = 'default') -> None:
        """
        Set up a clean test database for the specified alias.
        
        Args:
            db_alias: Database alias to set up (default: 'default')
        """
        connection = connections[db_alias]
        
        # Force close any existing connections
        connection.close()
        
        # Create fresh in-memory database for SQLite
        if connection.vendor == 'sqlite':
            self._setup_sqlite_test_db(db_alias)
        
        # Run migrations to set up schema
        self._migrate_test_database(db_alias)
    
    def teardown_test_database(self, db_alias: str = 'default') -> None:
        """
        Clean up test database and connections.
        
        Args:
            db_alias: Database alias to tear down (default: 'default')
        """
        connection = connections[db_alias]
        connection.close()
        
        # Clean up temp files if using file-based SQLite
        if connection.vendor == 'sqlite':
            self._cleanup_sqlite_test_db(db_alias)
    
    def reset_database(self, db_alias: str = 'default') -> None:
        """
        Reset database to clean state by flushing all data.
        
        Args:
            db_alias: Database alias to reset (default: 'default')
        """
        # Flush all data but keep schema
        call_command('flush', '--noinput', database=db_alias, verbosity=0)
    
    def create_test_database_file(self, prefix: str = 'test_db') -> str:
        """
        Create a temporary SQLite database file for testing.
        
        Args:
            prefix: Prefix for the temporary file name
            
        Returns:
            Path to the created database file
        """
        fd, db_path = tempfile.mkstemp(suffix='.db', prefix=prefix)
        os.close(fd)  # Close file descriptor, keep the file
        
        self.temp_db_files.append(db_path)
        return db_path
    
    def cleanup_temp_files(self) -> None:
        """Clean up all temporary database files created during testing."""
        for db_path in self.temp_db_files:
            try:
                if os.path.exists(db_path):
                    os.unlink(db_path)
            except OSError:
                pass  # File might already be deleted
        
        self.temp_db_files.clear()
    
    @contextmanager
    def isolated_database(self, db_alias: str = 'default'):
        """
        Context manager for running code with an isolated test database.
        
        Args:
            db_alias: Database alias to isolate
            
        Yields:
            Database connection for the isolated database
        """
        # Set up isolated database
        self.setup_test_database(db_alias)
        
        try:
            yield connections[db_alias]
        finally:
            # Clean up
            self.teardown_test_database(db_alias)
    
    @contextmanager
    def transaction_rollback(self, db_alias: str = 'default'):
        """
        Context manager that rolls back all database changes.
        
        Args:
            db_alias: Database alias to use for transaction
            
        Yields:
            Database connection within transaction
        """
        with transaction.atomic(using=db_alias):
            sid = transaction.savepoint(using=db_alias)
            try:
                yield connections[db_alias]
            finally:
                transaction.savepoint_rollback(sid, using=db_alias)
    
    def _setup_sqlite_test_db(self, db_alias: str) -> None:
        """Set up SQLite test database."""
        connection = connections[db_alias]
        
        # If using :memory:, no file setup needed
        if connection.settings_dict['NAME'] == ':memory:':
            return
        
        # If using file-based SQLite, ensure clean file
        db_path = connection.settings_dict['NAME']
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def _cleanup_sqlite_test_db(self, db_alias: str) -> None:
        """Clean up SQLite test database files."""
        connection = connections[db_alias]
        
        # Skip cleanup for in-memory databases
        if connection.settings_dict['NAME'] == ':memory:':
            return
        
        # Remove file-based database
        db_path = connection.settings_dict['NAME']
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except OSError:
                pass  # File might be locked or already deleted
    
    def _migrate_test_database(self, db_alias: str) -> None:
        """Run migrations for test database."""
        # Use --run-syncdb for faster test setup (no migration files)
        call_command(
            'migrate',
            '--run-syncdb',
            '--noinput',
            database=db_alias,
            verbosity=0
        )


class DatabaseStateManager:
    """
    Manages database state for testing including fixtures and data seeding.
    """
    
    def __init__(self, db_manager: Optional[TestDatabaseManager] = None):
        self.db_manager = db_manager or TestDatabaseManager()
        self.loaded_fixtures: List[str] = []
    
    def load_fixture(self, fixture_name: str, db_alias: str = 'default') -> None:
        """
        Load a test fixture into the database.
        
        Args:
            fixture_name: Name of the fixture to load
            db_alias: Database alias to load into
        """
        call_command('loaddata', fixture_name, database=db_alias, verbosity=0)
        self.loaded_fixtures.append(fixture_name)
    
    def create_test_user(self, username: str = 'testuser', email: str = 'test@example.com') -> Any:
        """
        Create a test user for authentication tests.
        
        Args:
            username: Username for the test user
            email: Email for the test user
            
        Returns:
            Created user instance
        """
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        return User.objects.create_user(
            username=username,
            email=email,
            password='testpass123'
        )
    
    def seed_test_data(self, data_set: str = 'minimal') -> None:
        """
        Seed database with test data.
        
        Args:
            data_set: Type of data set to seed ('minimal', 'standard', 'comprehensive')
        """
        if data_set == 'minimal':
            self._seed_minimal_data()
        elif data_set == 'standard':
            self._seed_standard_data()
        elif data_set == 'comprehensive':
            self._seed_comprehensive_data()
    
    def _seed_minimal_data(self) -> None:
        """Seed minimal test data."""
        # Create basic test user
        self.create_test_user()
    
    def _seed_standard_data(self) -> None:
        """Seed standard test data set."""
        self._seed_minimal_data()
        
        # Add additional standard test data
        # This would include roles, industries, etc.
        pass
    
    def _seed_comprehensive_data(self) -> None:
        """Seed comprehensive test data set."""
        self._seed_standard_data()
        
        # Add comprehensive test data
        # This would include full workflow scenarios
        pass


class DatabaseAssertions:
    """
    Provides assertion utilities for database testing.
    """
    
    @staticmethod
    def assert_table_exists(table_name: str, db_alias: str = 'default') -> bool:
        """
        Assert that a table exists in the database.
        
        Args:
            table_name: Name of the table to check
            db_alias: Database alias to check
            
        Returns:
            True if table exists, raises AssertionError otherwise
        """
        connection = connections[db_alias]
        
        with connection.cursor() as cursor:
            if connection.vendor == 'sqlite':
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    [table_name]
                )
                exists = cursor.fetchone() is not None
            else:
                # Add support for other database backends if needed
                raise NotImplementedError(f"Table existence check not implemented for {connection.vendor}")
        
        assert exists, f"Table '{table_name}' does not exist in database '{db_alias}'"
        return True
    
    @staticmethod
    def assert_table_empty(table_name: str, db_alias: str = 'default') -> bool:
        """
        Assert that a table is empty.
        
        Args:
            table_name: Name of the table to check
            db_alias: Database alias to check
            
        Returns:
            True if table is empty, raises AssertionError otherwise
        """
        connection = connections[db_alias]
        
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
        
        assert count == 0, f"Table '{table_name}' is not empty (contains {count} rows)"
        return True
    
    @staticmethod
    def assert_row_count(table_name: str, expected_count: int, db_alias: str = 'default') -> bool:
        """
        Assert that a table has the expected number of rows.
        
        Args:
            table_name: Name of the table to check
            expected_count: Expected number of rows
            db_alias: Database alias to check
            
        Returns:
            True if row count matches, raises AssertionError otherwise
        """
        connection = connections[db_alias]
        
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            actual_count = cursor.fetchone()[0]
        
        assert actual_count == expected_count, \
            f"Table '{table_name}' has {actual_count} rows, expected {expected_count}"
        return True


# Utility functions for common test database operations
def get_test_db_manager() -> TestDatabaseManager:
    """Get a test database manager instance."""
    return TestDatabaseManager()


def get_db_state_manager() -> DatabaseStateManager:
    """Get a database state manager instance."""
    return DatabaseStateManager()


def with_clean_database(func):
    """
    Decorator to run a test function with a clean database.
    
    Usage:
        @with_clean_database
        def test_something():
            # Test runs with clean database
            pass
    """
    def wrapper(*args, **kwargs):
        db_manager = TestDatabaseManager()
        
        with db_manager.isolated_database():
            return func(*args, **kwargs)
    
    return wrapper


def with_test_data(data_set: str = 'minimal'):
    """
    Decorator to run a test function with seeded test data.
    
    Args:
        data_set: Type of data set to seed ('minimal', 'standard', 'comprehensive')
    
    Usage:
        @with_test_data('standard')
        def test_something():
            # Test runs with standard test data
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            db_manager = TestDatabaseManager()
            state_manager = DatabaseStateManager(db_manager)
            
            with db_manager.isolated_database():
                state_manager.seed_test_data(data_set)
                return func(*args, **kwargs)
        
        return wrapper
    return decorator