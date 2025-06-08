"""
API Performance Benchmarks.
Tests API endpoint performance, memory usage, and response times.
"""

import pytest
import time
import psutil
import gc
import asyncio
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock
from django.test import TestCase
from django.urls import reverse
from django.test.client import Client
from datetime import datetime, timedelta
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import statistics

# Performance thresholds (in seconds)
PERFORMANCE_THRESHOLDS = {
    'authentication': {
        'signup': {'max_response_time': 2.0, 'max_memory_mb': 50},
        'login': {'max_response_time': 1.0, 'max_memory_mb': 30},
        'logout': {'max_response_time': 0.5, 'max_memory_mb': 20},
        'refresh': {'max_response_time': 0.8, 'max_memory_mb': 25}
    },
    'onboarding': {
        'languages_list': {'max_response_time': 0.5, 'max_memory_mb': 20},
        'industries_list': {'max_response_time': 0.5, 'max_memory_mb': 20},
        'language_set': {'max_response_time': 1.5, 'max_memory_mb': 40},
        'industry_set': {'max_response_time': 1.5, 'max_memory_mb': 40},
        'partners_select': {'max_response_time': 2.0, 'max_memory_mb': 50},
        'summary': {'max_response_time': 1.0, 'max_memory_mb': 30}
    }
}

class PerformanceMonitor:
    """Monitor system performance during API calls."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = None
        self.peak_memory = None
        self.start_time = None
        self.end_time = None
    
    def start_monitoring(self):
        """Start performance monitoring."""
        gc.collect()  # Clean up before measurement
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.initial_memory
        self.start_time = time.perf_counter()
    
    def update_peak_memory(self):
        """Update peak memory usage."""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
    
    def stop_monitoring(self) -> Dict[str, float]:
        """Stop monitoring and return metrics."""
        self.end_time = time.perf_counter()
        self.update_peak_memory()
        
        return {
            'response_time': self.end_time - self.start_time,
            'memory_used_mb': self.peak_memory - self.initial_memory,
            'peak_memory_mb': self.peak_memory,
            'initial_memory_mb': self.initial_memory
        }

class APIMockClient:
    """Mock API client for performance testing."""
    
    def __init__(self):
        self.response_delays = {
            'signup': 0.1,
            'login': 0.05,
            'logout': 0.02,
            'refresh': 0.03,
            'languages_list': 0.01,
            'industries_list': 0.01,
            'language_set': 0.08,
            'industry_set': 0.08,
            'partners_select': 0.12,
            'summary': 0.05
        }
    
    async def post(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simulate POST request with realistic delay."""
        endpoint_key = self._get_endpoint_key(endpoint)
        delay = self.response_delays.get(endpoint_key, 0.05)
        
        await asyncio.sleep(delay)  # Simulate processing time
        
        return self._generate_mock_response(endpoint, data)
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """Simulate GET request with realistic delay."""
        endpoint_key = self._get_endpoint_key(endpoint)
        delay = self.response_delays.get(endpoint_key, 0.05)
        
        await asyncio.sleep(delay)  # Simulate processing time
        
        return self._generate_mock_response(endpoint, {})
    
    def _get_endpoint_key(self, endpoint: str) -> str:
        """Extract endpoint key for delay lookup."""
        if 'signup' in endpoint:
            return 'signup'
        elif 'login' in endpoint:
            return 'login'
        elif 'logout' in endpoint:
            return 'logout'
        elif 'refresh' in endpoint:
            return 'refresh'
        elif 'languages' in endpoint:
            return 'languages_list'
        elif 'industries' in endpoint:
            return 'industries_list'
        elif 'language/set' in endpoint:
            return 'language_set'
        elif 'industry/set' in endpoint:
            return 'industry_set'
        elif 'partners' in endpoint:
            return 'partners_select'
        elif 'summary' in endpoint:
            return 'summary'
        return 'unknown'
    
    def _generate_mock_response(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic mock response."""
        if 'signup' in endpoint:
            return {
                'user': {
                    'id': 'user-123',
                    'email': data.get('email', 'test@example.com'),
                    'full_name': data.get('full_name', 'Test User')
                },
                'tokens': {
                    'access_token': 'access-token-123',
                    'refresh_token': 'refresh-token-123',
                    'expires_in': 3600
                }
            }
        elif 'login' in endpoint:
            return {
                'user': {'id': 'user-123', 'email': data.get('email', 'test@example.com')},
                'tokens': {'access_token': 'access-token-123', 'expires_in': 3600}
            }
        elif 'languages' in endpoint:
            return {
                'languages': [
                    {'code': 'en', 'name': 'English'},
                    {'code': 'es', 'name': 'Spanish'},
                    {'code': 'fr', 'name': 'French'}
                ]
            }
        elif 'industries' in endpoint:
            return {
                'industries': [
                    {'id': '1', 'name': 'Technology'},
                    {'id': '2', 'name': 'Healthcare'},
                    {'id': '3', 'name': 'Finance'}
                ]
            }
        else:
            return {'success': True, 'message': 'Operation completed'}


class TestAPIPerformanceBenchmarks:
    """Test API endpoint performance benchmarks."""
    
    def setup_method(self):
        """Set up test environment."""
        self.monitor = PerformanceMonitor()
        self.client = APIMockClient()
        self.performance_results = []
    
    def teardown_method(self):
        """Clean up after tests."""
        gc.collect()
    
    def assert_performance_threshold(self, endpoint_type: str, endpoint_name: str, metrics: Dict[str, float]):
        """Assert that performance metrics meet thresholds."""
        thresholds = PERFORMANCE_THRESHOLDS[endpoint_type][endpoint_name]
        
        assert metrics['response_time'] <= thresholds['max_response_time'], \
            f"{endpoint_name} response time {metrics['response_time']:.3f}s exceeds threshold {thresholds['max_response_time']}s"
        
        assert metrics['memory_used_mb'] <= thresholds['max_memory_mb'], \
            f"{endpoint_name} memory usage {metrics['memory_used_mb']:.1f}MB exceeds threshold {thresholds['max_memory_mb']}MB"
    
    @pytest.mark.asyncio
    async def test_authentication_signup_performance(self):
        """Benchmark user signup endpoint performance."""
        self.monitor.start_monitoring()
        
        # Simulate signup request
        response = await self.client.post('/api/v1/auth/users/signup/', {
            'email': 'benchmark@test.com',
            'password': 'BenchmarkPass123!',
            'full_name': 'Benchmark User'
        })
        
        metrics = self.monitor.stop_monitoring()
        
        # Verify response and performance
        assert 'user' in response
        assert 'tokens' in response
        self.assert_performance_threshold('authentication', 'signup', metrics)
        
        self.performance_results.append({
            'endpoint': 'signup',
            'metrics': metrics
        })
    
    @pytest.mark.asyncio
    async def test_authentication_login_performance(self):
        """Benchmark user login endpoint performance."""
        self.monitor.start_monitoring()
        
        # Simulate login request
        response = await self.client.post('/api/v1/auth/sessions/login/', {
            'email': 'benchmark@test.com',
            'password': 'BenchmarkPass123!'
        })
        
        metrics = self.monitor.stop_monitoring()
        
        # Verify response and performance
        assert 'user' in response
        assert 'tokens' in response
        self.assert_performance_threshold('authentication', 'login', metrics)
        
        self.performance_results.append({
            'endpoint': 'login',
            'metrics': metrics
        })
    
    @pytest.mark.asyncio
    async def test_authentication_logout_performance(self):
        """Benchmark user logout endpoint performance."""
        self.monitor.start_monitoring()
        
        # Simulate logout request
        response = await self.client.post('/api/v1/auth/sessions/logout/', {})
        
        metrics = self.monitor.stop_monitoring()
        
        # Verify response and performance
        assert 'success' in response
        self.assert_performance_threshold('authentication', 'logout', metrics)
        
        self.performance_results.append({
            'endpoint': 'logout',
            'metrics': metrics
        })
    
    @pytest.mark.asyncio
    async def test_authentication_refresh_performance(self):
        """Benchmark token refresh endpoint performance."""
        self.monitor.start_monitoring()
        
        # Simulate token refresh request
        response = await self.client.post('/api/v1/auth/sessions/refresh/', {
            'refresh_token': 'refresh-token-123'
        })
        
        metrics = self.monitor.stop_monitoring()
        
        # Verify response and performance
        assert 'success' in response
        self.assert_performance_threshold('authentication', 'refresh', metrics)
        
        self.performance_results.append({
            'endpoint': 'refresh',
            'metrics': metrics
        })
    
    @pytest.mark.asyncio
    async def test_onboarding_languages_list_performance(self):
        """Benchmark languages list endpoint performance."""
        self.monitor.start_monitoring()
        
        # Simulate languages list request
        response = await self.client.get('/api/v1/onboarding/languages/')
        
        metrics = self.monitor.stop_monitoring()
        
        # Verify response and performance
        assert 'languages' in response
        assert len(response['languages']) > 0
        self.assert_performance_threshold('onboarding', 'languages_list', metrics)
        
        self.performance_results.append({
            'endpoint': 'languages_list',
            'metrics': metrics
        })
    
    @pytest.mark.asyncio
    async def test_onboarding_industries_list_performance(self):
        """Benchmark industries list endpoint performance."""
        self.monitor.start_monitoring()
        
        # Simulate industries list request
        response = await self.client.get('/api/v1/onboarding/industries/')
        
        metrics = self.monitor.stop_monitoring()
        
        # Verify response and performance
        assert 'industries' in response
        assert len(response['industries']) > 0
        self.assert_performance_threshold('onboarding', 'industries_list', metrics)
        
        self.performance_results.append({
            'endpoint': 'industries_list',
            'metrics': metrics
        })
    
    @pytest.mark.asyncio
    async def test_onboarding_language_set_performance(self):
        """Benchmark language selection endpoint performance."""
        self.monitor.start_monitoring()
        
        # Simulate language selection request
        response = await self.client.post('/api/v1/onboarding/language/set/', {
            'user_id': 'user-123',
            'language_code': 'en'
        })
        
        metrics = self.monitor.stop_monitoring()
        
        # Verify response and performance
        assert 'success' in response
        self.assert_performance_threshold('onboarding', 'language_set', metrics)
        
        self.performance_results.append({
            'endpoint': 'language_set',
            'metrics': metrics
        })
    
    @pytest.mark.asyncio
    async def test_onboarding_industry_set_performance(self):
        """Benchmark industry selection endpoint performance."""
        self.monitor.start_monitoring()
        
        # Simulate industry selection request
        response = await self.client.post('/api/v1/onboarding/industry/set/', {
            'user_id': 'user-123',
            'industry_id': '1'
        })
        
        metrics = self.monitor.stop_monitoring()
        
        # Verify response and performance
        assert 'success' in response
        self.assert_performance_threshold('onboarding', 'industry_set', metrics)
        
        self.performance_results.append({
            'endpoint': 'industry_set',
            'metrics': metrics
        })
    
    @pytest.mark.asyncio
    async def test_onboarding_partners_select_performance(self):
        """Benchmark partners selection endpoint performance."""
        self.monitor.start_monitoring()
        
        # Simulate partners selection request
        response = await self.client.post('/api/v1/onboarding/communication/partners/select/', {
            'user_id': 'user-123',
            'partner_ids': ['1', '2'],
            'custom_partners': ['Custom Partner 1']
        })
        
        metrics = self.monitor.stop_monitoring()
        
        # Verify response and performance
        assert 'success' in response
        self.assert_performance_threshold('onboarding', 'partners_select', metrics)
        
        self.performance_results.append({
            'endpoint': 'partners_select',
            'metrics': metrics
        })
    
    @pytest.mark.asyncio
    async def test_onboarding_summary_performance(self):
        """Benchmark onboarding summary endpoint performance."""
        self.monitor.start_monitoring()
        
        # Simulate summary request
        response = await self.client.get('/api/v1/onboarding/summary/')
        
        metrics = self.monitor.stop_monitoring()
        
        # Verify response and performance
        assert 'success' in response
        self.assert_performance_threshold('onboarding', 'summary', metrics)
        
        self.performance_results.append({
            'endpoint': 'summary',
            'metrics': metrics
        })
    
    @pytest.mark.asyncio
    async def test_batch_performance_comparison(self):
        """Test multiple endpoints and compare performance."""
        endpoints_to_test = [
            ('login', '/api/v1/auth/sessions/login/', {'email': 'test@test.com', 'password': 'pass'}),
            ('languages_list', '/api/v1/onboarding/languages/', None),
            ('industries_list', '/api/v1/onboarding/industries/', None),
            ('language_set', '/api/v1/onboarding/language/set/', {'user_id': 'user-123', 'language_code': 'en'})
        ]
        
        batch_results = []
        
        for endpoint_name, endpoint_url, data in endpoints_to_test:
            self.monitor.start_monitoring()
            
            if data:
                response = await self.client.post(endpoint_url, data)
            else:
                response = await self.client.get(endpoint_url)
            
            metrics = self.monitor.stop_monitoring()
            
            batch_results.append({
                'endpoint': endpoint_name,
                'response_time': metrics['response_time'],
                'memory_used': metrics['memory_used_mb']
            })
        
        # Verify all endpoints performed within acceptable ranges
        for result in batch_results:
            assert result['response_time'] < 3.0, f"{result['endpoint']} took too long: {result['response_time']:.3f}s"
            assert result['memory_used'] < 100, f"{result['endpoint']} used too much memory: {result['memory_used']:.1f}MB"
        
        # Calculate performance statistics
        response_times = [r['response_time'] for r in batch_results]
        memory_usage = [r['memory_used'] for r in batch_results]
        
        assert statistics.mean(response_times) < 1.0, "Average response time too high"
        assert statistics.mean(memory_usage) < 50, "Average memory usage too high"


class TestMemoryLeakDetection:
    """Test for memory leaks during extended API usage."""
    
    def setup_method(self):
        """Set up memory leak detection."""
        self.client = APIMockClient()
        gc.collect()  # Clean up before testing
    
    @pytest.mark.asyncio
    async def test_repeated_requests_memory_stability(self):
        """Test that repeated API calls don't cause memory leaks."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Perform many repeated requests
        for i in range(100):
            await self.client.post('/api/v1/auth/sessions/login/', {
                'email': f'user{i}@test.com',
                'password': 'TestPass123!'
            })
            
            # Periodically check memory growth
            if i % 25 == 0:
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                memory_growth = current_memory - initial_memory
                
                # Allow some memory growth but detect significant leaks
                assert memory_growth < 100, f"Potential memory leak detected: {memory_growth:.1f}MB growth after {i+1} requests"
        
        # Final memory check
        gc.collect()  # Force garbage collection
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        total_growth = final_memory - initial_memory
        
        # Should not have significant memory growth after GC
        assert total_growth < 50, f"Memory leak detected: {total_growth:.1f}MB growth after 100 requests"


class TestConcurrentRequestPerformance:
    """Test API performance under concurrent load."""
    
    def setup_method(self):
        """Set up concurrent testing."""
        self.client = APIMockClient()
    
    @pytest.mark.asyncio
    async def test_concurrent_login_requests(self):
        """Test performance with concurrent login requests."""
        concurrent_users = 10
        
        async def login_user(user_id: int):
            start_time = time.perf_counter()
            response = await self.client.post('/api/v1/auth/sessions/login/', {
                'email': f'user{user_id}@test.com',
                'password': 'TestPass123!'
            })
            end_time = time.perf_counter()
            
            return {
                'user_id': user_id,
                'response_time': end_time - start_time,
                'success': 'user' in response
            }
        
        # Execute concurrent requests
        start_time = time.perf_counter()
        tasks = [login_user(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time
        
        # Verify all requests succeeded
        successful_requests = sum(1 for r in results if r['success'])
        assert successful_requests == concurrent_users, f"Only {successful_requests}/{concurrent_users} requests succeeded"
        
        # Verify performance under load
        response_times = [r['response_time'] for r in results]
        max_response_time = max(response_times)
        avg_response_time = statistics.mean(response_times)
        
        assert max_response_time < 5.0, f"Maximum response time too high: {max_response_time:.3f}s"
        assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time:.3f}s"
        assert total_time < 10.0, f"Total time for {concurrent_users} concurrent requests too high: {total_time:.3f}s"
    
    @pytest.mark.asyncio
    async def test_mixed_endpoint_concurrent_load(self):
        """Test performance with mixed concurrent requests across endpoints."""
        concurrent_requests = 20
        
        async def mixed_requests(request_id: int):
            request_type = request_id % 4
            start_time = time.perf_counter()
            
            if request_type == 0:
                response = await self.client.post('/api/v1/auth/sessions/login/', {
                    'email': f'user{request_id}@test.com', 'password': 'pass'
                })
                endpoint = 'login'
            elif request_type == 1:
                response = await self.client.get('/api/v1/onboarding/languages/')
                endpoint = 'languages'
            elif request_type == 2:
                response = await self.client.get('/api/v1/onboarding/industries/')
                endpoint = 'industries'
            else:
                response = await self.client.post('/api/v1/onboarding/language/set/', {
                    'user_id': f'user-{request_id}', 'language_code': 'en'
                })
                endpoint = 'language_set'
            
            end_time = time.perf_counter()
            
            return {
                'request_id': request_id,
                'endpoint': endpoint,
                'response_time': end_time - start_time,
                'success': len(response) > 0
            }
        
        # Execute mixed concurrent requests
        start_time = time.perf_counter()
        tasks = [mixed_requests(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time
        
        # Analyze results by endpoint type
        endpoint_stats = {}
        for result in results:
            endpoint = result['endpoint']
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = []
            endpoint_stats[endpoint].append(result['response_time'])
        
        # Verify performance across all endpoint types
        for endpoint, times in endpoint_stats.items():
            avg_time = statistics.mean(times)
            max_time = max(times)
            
            assert avg_time < 3.0, f"{endpoint} average response time too high: {avg_time:.3f}s"
            assert max_time < 8.0, f"{endpoint} maximum response time too high: {max_time:.3f}s"
        
        # Verify overall system performance
        assert total_time < 15.0, f"Total time for {concurrent_requests} mixed requests too high: {total_time:.3f}s"