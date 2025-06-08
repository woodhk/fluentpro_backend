"""
Integration tests for database setup, teardown, and management.
Tests the test database configuration and utilities.
"""

import pytest
import tempfile
import os
from django.test import TestCase, TransactionTestCase
from django.db import connections, transaction
from django.core.management import call_command
from django.contrib.auth import get_user_model

from tests.utils.database import (
    TestDatabaseManager, DatabaseStateManager, DatabaseAssertions,
    get_test_db_manager, get_db_state_manager, with_clean_database, with_test_data
)


class TestDatabaseSetupTeardown(TestCase):
    """Test database setup and teardown functionality."""
    
    def setUp(self):
        """Set up test database manager."""
        self.db_manager = TestDatabaseManager()
    
    def tearDown(self):
        """Clean up after tests."""
        self.db_manager.cleanup_temp_files()
    
    def test_database_is_sqlite_in_memory(self):
        """Test that test database uses SQLite in-memory."""
        connection = connections['default']
        
        # Verify it's SQLite
        self.assertEqual(connection.vendor, 'sqlite')
        
        # Verify it's in-memory
        db_name = connection.settings_dict['NAME']
        self.assertEqual(db_name, ':memory:')
    
    def test_database_isolation_between_tests(self):
        """Test that database state is isolated between tests."""
        User = get_user_model()
        
        # Create a user
        user = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass'
        )
        
        # Verify user exists
        self.assertTrue(User.objects.filter(username='testuser1').exists())
        
        # This test should not see data from other tests
        self.assertEqual(User.objects.count(), 1)
    
    def test_database_reset_functionality(self):
        """Test that database can be reset to clean state."""
        User = get_user_model()
        
        # Create test data
        User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass'
        )
        
        # Verify data exists
        self.assertEqual(User.objects.count(), 1)
        
        # Reset database
        self.db_manager.reset_database()
        
        # Verify data is gone
        self.assertEqual(User.objects.count(), 0)
    
    def test_temp_database_file_creation(self):
        """Test creation and cleanup of temporary database files."""
        # Create temp database file
        db_path = self.db_manager.create_test_database_file('test_temp')
        
        # Verify file was created
        self.assertTrue(os.path.exists(db_path))
        self.assertTrue(db_path.endswith('.db'))
        self.assertIn('test_temp', db_path)
        
        # Cleanup
        self.db_manager.cleanup_temp_files()
        
        # Verify file was removed
        self.assertFalse(os.path.exists(db_path))
    
    def test_isolated_database_context_manager(self):
        """Test isolated database context manager."""
        User = get_user_model()
        
        # Create user outside context
        User.objects.create_user(
            username='outside_user',
            email='outside@example.com',
            password='testpass'
        )
        
        initial_count = User.objects.count()
        
        # Use isolated database context
        with self.db_manager.isolated_database() as connection:
            # Verify we have a clean database
            self.assertEqual(User.objects.count(), 0)
            
            # Create user in isolated context
            User.objects.create_user(
                username='isolated_user',
                email='isolated@example.com',
                password='testpass'
            )
            
            self.assertEqual(User.objects.count(), 1)
        
        # After context, should be back to original state
        self.assertEqual(User.objects.count(), initial_count)
    
    def test_transaction_rollback_context_manager(self):
        """Test transaction rollback context manager."""
        User = get_user_model()
        
        initial_count = User.objects.count()
        
        # Use transaction rollback context
        with self.db_manager.transaction_rollback() as connection:
            # Create user in transaction
            User.objects.create_user(
                username='rollback_user',
                email='rollback@example.com',
                password='testpass'
            )
            
            # Verify user exists within transaction
            self.assertEqual(User.objects.count(), initial_count + 1)
        
        # After rollback, user should not exist
        self.assertEqual(User.objects.count(), initial_count)


class TestDatabaseStateManager(TestCase):
    """Test database state management functionality."""
    
    def setUp(self):
        """Set up database state manager."""
        self.state_manager = DatabaseStateManager()
    
    def test_create_test_user(self):
        """Test creation of test users."""
        User = get_user_model()
        
        # Create test user
        user = self.state_manager.create_test_user(
            username='statetest',
            email='statetest@example.com'
        )
        
        # Verify user was created
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'statetest')
        self.assertEqual(user.email, 'statetest@example.com')
        
        # Verify user exists in database
        self.assertTrue(User.objects.filter(username='statetest').exists())
    
    def test_seed_minimal_data(self):
        """Test seeding minimal test data."""
        User = get_user_model()
        
        # Start with empty database
        self.assertEqual(User.objects.count(), 0)
        
        # Seed minimal data
        self.state_manager.seed_test_data('minimal')
        
        # Verify basic test user was created
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.filter(username='testuser').exists())
    
    def test_seed_standard_data(self):
        """Test seeding standard test data."""
        User = get_user_model()
        
        # Seed standard data
        self.state_manager.seed_test_data('standard')
        
        # Verify data was seeded (includes minimal + additional)
        self.assertGreaterEqual(User.objects.count(), 1)
    
    def test_seed_comprehensive_data(self):
        """Test seeding comprehensive test data."""
        User = get_user_model()
        
        # Seed comprehensive data
        self.state_manager.seed_test_data('comprehensive')
        
        # Verify data was seeded (includes standard + additional)
        self.assertGreaterEqual(User.objects.count(), 1)


class TestDatabaseAssertions(TestCase):
    """Test database assertion utilities."""
    
    def test_assert_table_exists(self):
        """Test table existence assertion."""
        # Test with existing table
        self.assertTrue(DatabaseAssertions.assert_table_exists('auth_user'))
        
        # Test with non-existing table
        with self.assertRaises(AssertionError):
            DatabaseAssertions.assert_table_exists('nonexistent_table')
    
    def test_assert_table_empty(self):
        """Test table emptiness assertion."""
        User = get_user_model()
        
        # Empty table should pass
        self.assertTrue(DatabaseAssertions.assert_table_empty('auth_user'))
        
        # Create user
        User.objects.create_user(
            username='emptytest',
            email='empty@example.com',
            password='testpass'
        )
        
        # Non-empty table should fail
        with self.assertRaises(AssertionError):
            DatabaseAssertions.assert_table_empty('auth_user')
    
    def test_assert_row_count(self):
        """Test row count assertion."""
        User = get_user_model()
        
        # Test with correct count
        self.assertTrue(DatabaseAssertions.assert_row_count('auth_user', 0))
        
        # Create users
        User.objects.create_user(
            username='count1',
            email='count1@example.com',
            password='testpass'
        )
        User.objects.create_user(
            username='count2',
            email='count2@example.com',
            password='testpass'
        )
        
        # Test with correct count
        self.assertTrue(DatabaseAssertions.assert_row_count('auth_user', 2))
        
        # Test with incorrect count
        with self.assertRaises(AssertionError):
            DatabaseAssertions.assert_row_count('auth_user', 5)


class TestDatabaseUtilityFunctions(TestCase):
    """Test utility functions for database testing."""
    
    def test_get_test_db_manager(self):
        """Test getting test database manager instance."""
        manager = get_test_db_manager()
        self.assertIsInstance(manager, TestDatabaseManager)
    
    def test_get_db_state_manager(self):
        """Test getting database state manager instance."""
        manager = get_db_state_manager()
        self.assertIsInstance(manager, DatabaseStateManager)


class TestDatabaseDecorators(TestCase):
    """Test database decorators functionality."""
    
    def test_with_clean_database_decorator(self):
        """Test with_clean_database decorator."""
        User = get_user_model()
        
        # Create user outside decorated function
        User.objects.create_user(
            username='outside_decorator',
            email='outside@example.com',
            password='testpass'
        )
        
        @with_clean_database
        def decorated_test():
            # Should start with clean database
            self.assertEqual(User.objects.count(), 0)
            
            # Create user in decorated function
            User.objects.create_user(
                username='inside_decorator',
                email='inside@example.com',
                password='testpass'
            )
            
            self.assertEqual(User.objects.count(), 1)
        
        # Run decorated test
        decorated_test()
        
        # Original data should still exist after decorated function
        self.assertTrue(User.objects.filter(username='outside_decorator').exists())
    
    def test_with_test_data_decorator(self):
        """Test with_test_data decorator."""
        User = get_user_model()
        
        @with_test_data('minimal')
        def decorated_test():
            # Should have minimal test data
            self.assertGreaterEqual(User.objects.count(), 1)
            self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # Run decorated test
        decorated_test()


class TestDatabaseConfiguration(TestCase):
    """Test database configuration for testing environment."""
    
    def test_testing_settings_applied(self):
        """Test that testing settings are properly applied."""
        from django.conf import settings
        
        # Verify testing mode is enabled
        self.assertTrue(getattr(settings, 'TESTING', False))
        
        # Verify SQLite in-memory database
        db_config = settings.DATABASES['default']
        self.assertEqual(db_config['ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(db_config['NAME'], ':memory:')
    
    def test_cache_configuration(self):
        """Test that cache is configured for testing."""
        from django.conf import settings
        
        cache_config = settings.CACHES['default']
        self.assertEqual(cache_config['BACKEND'], 'django.core.cache.backends.locmem.LocMemCache')
    
    def test_celery_eager_mode(self):
        """Test that Celery is in eager mode for testing."""
        from django.conf import settings
        
        self.assertTrue(settings.CELERY_TASK_ALWAYS_EAGER)
        self.assertTrue(settings.CELERY_TASK_EAGER_PROPAGATES)
    
    def test_external_services_mocked(self):
        """Test that external services are configured for mocking."""
        from django.conf import settings
        
        # Verify mock configuration flags
        self.assertTrue(settings.MOCK_EXTERNAL_SERVICES)
        self.assertTrue(settings.MOCK_AI_SERVICES)
        self.assertTrue(settings.MOCK_AUTH_SERVICES)
    
    def test_performance_settings(self):
        """Test performance-related testing settings."""
        from django.conf import settings
        
        # Verify performance monitoring is disabled
        self.assertFalse(settings.PERFORMANCE_MONITORING_ENABLED)
        
        # Verify feature flags for testing
        feature_flags = settings.FEATURE_FLAGS
        self.assertFalse(feature_flags['ENABLE_BACKGROUND_TASKS'])
        self.assertFalse(feature_flags['ENABLE_METRICS_COLLECTION'])
        self.assertFalse(feature_flags['ENABLE_DISTRIBUTED_TRACING'])


class TestDatabaseMigrations(TransactionTestCase):
    """Test database migration handling in testing environment."""
    
    def test_migrations_disabled(self):
        """Test that migrations are disabled for faster tests."""
        from django.conf import settings
        
        # Verify DisableMigrations is configured
        migration_modules = settings.MIGRATION_MODULES
        self.assertIsNotNone(migration_modules)
        
        # Test that it contains all apps
        self.assertIn('auth', migration_modules)
    
    def test_schema_creation_via_syncdb(self):
        """Test that schema is created via syncdb for speed."""
        # This test verifies that the test database setup works
        # If we can run this test, syncdb worked correctly
        
        connection = connections['default']
        
        # Verify we can create tables
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_migration_table (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100)
                )
            """)
            
            cursor.execute("INSERT INTO test_migration_table (name) VALUES (?)", ['test'])
            cursor.execute("SELECT COUNT(*) FROM test_migration_table")
            count = cursor.fetchone()[0]
            
            self.assertEqual(count, 1)
            
            # Clean up
            cursor.execute("DROP TABLE test_migration_table")


# Performance tests for database operations
class TestDatabasePerformance(TestCase):
    """Test database performance in testing environment."""
    
    def test_database_connection_speed(self):
        """Test that database connections are fast."""
        import time
        
        start_time = time.time()
        
        # Perform database operation
        connection = connections['default']
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Should be very fast for in-memory SQLite
        self.assertLess(operation_time, 0.1)  # Less than 100ms
    
    def test_bulk_operations_performance(self):
        """Test performance of bulk database operations."""
        import time
        User = get_user_model()
        
        start_time = time.time()
        
        # Create multiple users
        users = [
            User(
                username=f'bulk_user_{i}',
                email=f'bulk{i}@example.com'
            )
            for i in range(100)
        ]
        
        User.objects.bulk_create(users)
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Bulk operations should be fast
        self.assertLess(operation_time, 1.0)  # Less than 1 second
        
        # Verify all users were created
        self.assertEqual(User.objects.count(), 100)


# Integration test for complete database workflow
class TestDatabaseWorkflow(TestCase):
    """Integration test for complete database testing workflow."""
    
    def test_complete_database_testing_workflow(self):
        """Test complete workflow from setup to teardown."""
        User = get_user_model()
        
        # 1. Start with clean database
        self.assertEqual(User.objects.count(), 0)
        DatabaseAssertions.assert_table_empty('auth_user')
        
        # 2. Create test data
        state_manager = DatabaseStateManager()
        state_manager.seed_test_data('minimal')
        
        # 3. Verify data was created
        self.assertGreater(User.objects.count(), 0)
        DatabaseAssertions.assert_row_count('auth_user', 1)
        
        # 4. Perform test operations
        test_user = User.objects.first()
        self.assertIsNotNone(test_user)
        
        # 5. Reset database
        db_manager = TestDatabaseManager()
        db_manager.reset_database()
        
        # 6. Verify clean state restored
        self.assertEqual(User.objects.count(), 0)
        DatabaseAssertions.assert_table_empty('auth_user')
    
    def test_database_isolation_across_test_methods(self):
        """Test that database isolation works across test methods."""
        User = get_user_model()
        
        # This test should start with a clean database
        # regardless of what previous tests did
        initial_count = User.objects.count()
        
        # Create a user
        User.objects.create_user(
            username='isolation_test',
            email='isolation@example.com',
            password='testpass'
        )
        
        # Verify user was created
        self.assertEqual(User.objects.count(), initial_count + 1)
        
        # The next test method should not see this user
        # due to Django's test isolation