"""
Load Testing with Concurrent User Simulation.
Tests system performance under realistic load conditions with multiple concurrent users.
"""

import pytest
import asyncio
import time
import random
import statistics
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import psutil
import threading
from dataclasses import dataclass
from enum import Enum
import json


class UserBehaviorPattern(Enum):
    """Different user behavior patterns for load testing."""
    QUICK_BROWSER = "quick_browser"  # Fast browsing, quick decisions
    THOROUGH_USER = "thorough_user"  # Takes time, reads everything
    TYPICAL_USER = "typical_user"    # Average user behavior
    POWER_USER = "power_user"        # Heavy usage patterns


@dataclass
class LoadTestConfig:
    """Configuration for load testing scenarios."""
    concurrent_users: int
    test_duration_seconds: int
    ramp_up_time_seconds: int
    user_behavior_pattern: UserBehaviorPattern
    target_throughput_requests_per_second: float
    max_acceptable_response_time: float
    max_acceptable_error_rate: float


@dataclass
class LoadTestResult:
    """Results from a load test execution."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    max_response_time: float
    requests_per_second: float
    error_rate: float
    peak_memory_usage_mb: float
    cpu_usage_percent: float
    test_duration: float


class MockLoadTestClient:
    """Mock client that simulates realistic API response times and behaviors."""
    
    def __init__(self, behavior_pattern: UserBehaviorPattern = UserBehaviorPattern.TYPICAL_USER):
        self.behavior_pattern = behavior_pattern
        self.session_data = {}
        self.request_count = 0
        
        # Define realistic response times based on endpoint complexity
        self.base_response_times = {
            'signup': 0.150,
            'login': 0.080,
            'logout': 0.030,
            'refresh': 0.040,
            'languages_list': 0.020,
            'industries_list': 0.025,
            'language_set': 0.120,
            'industry_set': 0.130,
            'partners_select': 0.200,
            'summary': 0.090,
            'role_match': 0.300  # AI-powered endpoint
        }
        
        # Adjust response times based on user behavior
        self.behavior_multipliers = {
            UserBehaviorPattern.QUICK_BROWSER: 0.8,
            UserBehaviorPattern.THOROUGH_USER: 1.3,
            UserBehaviorPattern.TYPICAL_USER: 1.0,
            UserBehaviorPattern.POWER_USER: 0.9
        }
    
    async def make_request(self, endpoint: str, method: str = 'POST', data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simulate an API request with realistic timing and occasional failures."""
        self.request_count += 1
        
        # Simulate network latency and processing time
        base_time = self.base_response_times.get(endpoint, 0.100)
        behavior_multiplier = self.behavior_multipliers[self.behavior_pattern]
        
        # Add some randomness to simulate real-world variance
        variance = random.uniform(0.7, 1.3)
        response_time = base_time * behavior_multiplier * variance
        
        # Simulate occasional slow responses (network issues, database locks, etc.)
        if random.random() < 0.05:  # 5% chance of slow response
            response_time *= random.uniform(2.0, 5.0)
        
        # Simulate very rare failures
        if random.random() < 0.02:  # 2% chance of failure
            await asyncio.sleep(response_time)
            raise Exception(f"Simulated {endpoint} failure")
        
        await asyncio.sleep(response_time)
        
        return self._generate_response(endpoint, method, data)
    
    def _generate_response(self, endpoint: str, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock response data."""
        user_id = f"load-test-user-{random.randint(1000, 9999)}"
        
        responses = {
            'signup': {
                'user': {'id': user_id, 'email': data.get('email', 'test@example.com')},
                'tokens': {'access_token': f'token-{user_id}', 'expires_in': 3600}
            },
            'login': {
                'user': {'id': user_id, 'email': data.get('email', 'test@example.com')},
                'tokens': {'access_token': f'token-{user_id}', 'expires_in': 3600}
            },
            'languages_list': {
                'languages': [{'code': 'en', 'name': 'English'}, {'code': 'es', 'name': 'Spanish'}]
            },
            'industries_list': {
                'industries': [{'id': '1', 'name': 'Technology'}, {'id': '2', 'name': 'Healthcare'}]
            }
        }
        
        return responses.get(endpoint, {'success': True, 'message': f'{endpoint} completed'})


class UserSimulator:
    """Simulates a single user's journey through the application."""
    
    def __init__(self, user_id: int, behavior_pattern: UserBehaviorPattern):
        self.user_id = user_id
        self.behavior_pattern = behavior_pattern
        self.client = MockLoadTestClient(behavior_pattern)
        self.results = []
        self.session_start_time = None
    
    async def simulate_full_user_journey(self) -> List[Dict[str, Any]]:
        """Simulate a complete user journey from signup to onboarding completion."""
        self.session_start_time = time.perf_counter()
        
        try:
            # Step 1: User Registration
            await self._perform_signup()
            
            # Step 2: Login (some users might logout and login again)
            if random.random() < 0.3:  # 30% of users logout and login again
                await self._perform_logout()
                await self._perform_login()
            
            # Step 3: Browse available options
            await self._browse_languages()
            await self._browse_industries()
            
            # Step 4: Make selections (with thinking time)
            await self._select_language()
            await self._add_thinking_time()
            await self._select_industry()
            await self._add_thinking_time()
            
            # Step 5: Select communication partners
            await self._select_partners()
            
            # Step 6: View summary (some users check multiple times)
            await self._view_summary()
            if random.random() < 0.4:  # 40% check summary again
                await self._add_thinking_time()
                await self._view_summary()
        
        except Exception as e:
            self._record_error(str(e))
        
        return self.results
    
    async def simulate_browsing_behavior(self, duration_seconds: int) -> List[Dict[str, Any]]:
        """Simulate user browsing behavior for a specified duration."""
        self.session_start_time = time.perf_counter()
        end_time = self.session_start_time + duration_seconds
        
        # Login first
        await self._perform_login()
        
        while time.perf_counter() < end_time:
            # Random browsing actions
            actions = [
                self._browse_languages,
                self._browse_industries,
                self._view_summary,
                self._select_language,
                self._select_industry
            ]
            
            action = random.choice(actions)
            try:
                await action()
                await self._add_thinking_time()
            except Exception as e:
                self._record_error(str(e))
        
        return self.results
    
    async def _perform_signup(self):
        """Simulate user signup."""
        start_time = time.perf_counter()
        try:
            response = await self.client.make_request('signup', 'POST', {
                'email': f'loadtest{self.user_id}@example.com',
                'password': 'LoadTest123!',
                'full_name': f'Load Test User {self.user_id}'
            })
            self._record_success('signup', start_time)
        except Exception as e:
            self._record_failure('signup', start_time, str(e))
    
    async def _perform_login(self):
        """Simulate user login."""
        start_time = time.perf_counter()
        try:
            response = await self.client.make_request('login', 'POST', {
                'email': f'loadtest{self.user_id}@example.com',
                'password': 'LoadTest123!'
            })
            self._record_success('login', start_time)
        except Exception as e:
            self._record_failure('login', start_time, str(e))
    
    async def _perform_logout(self):
        """Simulate user logout."""
        start_time = time.perf_counter()
        try:
            response = await self.client.make_request('logout', 'POST', {})
            self._record_success('logout', start_time)
        except Exception as e:
            self._record_failure('logout', start_time, str(e))
    
    async def _browse_languages(self):
        """Simulate browsing available languages."""
        start_time = time.perf_counter()
        try:
            response = await self.client.make_request('languages_list', 'GET')
            self._record_success('languages_list', start_time)
        except Exception as e:
            self._record_failure('languages_list', start_time, str(e))
    
    async def _browse_industries(self):
        """Simulate browsing available industries."""
        start_time = time.perf_counter()
        try:
            response = await self.client.make_request('industries_list', 'GET')
            self._record_success('industries_list', start_time)
        except Exception as e:
            self._record_failure('industries_list', start_time, str(e))
    
    async def _select_language(self):
        """Simulate language selection."""
        start_time = time.perf_counter()
        try:
            response = await self.client.make_request('language_set', 'POST', {
                'user_id': f'user-{self.user_id}',
                'language_code': random.choice(['en', 'es', 'fr', 'de'])
            })
            self._record_success('language_set', start_time)
        except Exception as e:
            self._record_failure('language_set', start_time, str(e))
    
    async def _select_industry(self):
        """Simulate industry selection."""
        start_time = time.perf_counter()
        try:
            response = await self.client.make_request('industry_set', 'POST', {
                'user_id': f'user-{self.user_id}',
                'industry_id': str(random.randint(1, 5))
            })
            self._record_success('industry_set', start_time)
        except Exception as e:
            self._record_failure('industry_set', start_time, str(e))
    
    async def _select_partners(self):
        """Simulate communication partners selection."""
        start_time = time.perf_counter()
        try:
            response = await self.client.make_request('partners_select', 'POST', {
                'user_id': f'user-{self.user_id}',
                'partner_ids': [str(random.randint(1, 3)) for _ in range(random.randint(1, 3))],
                'custom_partners': ['Custom Partner'] if random.random() < 0.3 else []
            })
            self._record_success('partners_select', start_time)
        except Exception as e:
            self._record_failure('partners_select', start_time, str(e))
    
    async def _view_summary(self):
        """Simulate viewing onboarding summary."""
        start_time = time.perf_counter()
        try:
            response = await self.client.make_request('summary', 'GET')
            self._record_success('summary', start_time)
        except Exception as e:
            self._record_failure('summary', start_time, str(e))
    
    async def _add_thinking_time(self):
        """Add realistic thinking/reading time between actions."""
        thinking_times = {
            UserBehaviorPattern.QUICK_BROWSER: random.uniform(0.5, 2.0),
            UserBehaviorPattern.THOROUGH_USER: random.uniform(3.0, 8.0),
            UserBehaviorPattern.TYPICAL_USER: random.uniform(1.5, 4.0),
            UserBehaviorPattern.POWER_USER: random.uniform(0.2, 1.0)
        }
        
        thinking_time = thinking_times[self.behavior_pattern]
        await asyncio.sleep(thinking_time)
    
    def _record_success(self, endpoint: str, start_time: float):
        """Record successful request."""
        end_time = time.perf_counter()
        self.results.append({
            'user_id': self.user_id,
            'endpoint': endpoint,
            'success': True,
            'response_time': end_time - start_time,
            'timestamp': datetime.now().isoformat(),
            'error': None
        })
    
    def _record_failure(self, endpoint: str, start_time: float, error: str):
        """Record failed request."""
        end_time = time.perf_counter()
        self.results.append({
            'user_id': self.user_id,
            'endpoint': endpoint,
            'success': False,
            'response_time': end_time - start_time,
            'timestamp': datetime.now().isoformat(),
            'error': error
        })
    
    def _record_error(self, error: str):
        """Record general error."""
        self.results.append({
            'user_id': self.user_id,
            'endpoint': 'general',
            'success': False,
            'response_time': 0,
            'timestamp': datetime.now().isoformat(),
            'error': error
        })


class LoadTestOrchestrator:
    """Orchestrates load testing scenarios with multiple concurrent users."""
    
    def __init__(self):
        self.system_monitor = None
        self.monitoring_active = False
        self.cpu_usage_samples = []
        self.memory_usage_samples = []
    
    async def run_load_test(self, config: LoadTestConfig) -> LoadTestResult:
        """Run a complete load test scenario."""
        print(f"Starting load test: {config.concurrent_users} users, {config.test_duration_seconds}s duration")
        
        # Start system monitoring
        self._start_system_monitoring()
        
        try:
            # Create user simulators with varied behavior patterns
            simulators = self._create_user_simulators(config)
            
            # Execute load test with ramp-up
            all_results = await self._execute_with_ramp_up(simulators, config)
            
            # Analyze results
            return self._analyze_results(all_results, config)
        
        finally:
            # Stop system monitoring
            self._stop_system_monitoring()
    
    def _create_user_simulators(self, config: LoadTestConfig) -> List[UserSimulator]:
        """Create user simulators with varied behavior patterns."""
        simulators = []
        
        # Distribute behavior patterns realistically
        behavior_distribution = {
            UserBehaviorPattern.QUICK_BROWSER: 0.25,
            UserBehaviorPattern.TYPICAL_USER: 0.50,
            UserBehaviorPattern.THOROUGH_USER: 0.20,
            UserBehaviorPattern.POWER_USER: 0.05
        }
        
        for i in range(config.concurrent_users):
            # Select behavior pattern based on distribution
            rand = random.random()
            cumulative = 0
            selected_behavior = UserBehaviorPattern.TYPICAL_USER
            
            for behavior, probability in behavior_distribution.items():
                cumulative += probability
                if rand <= cumulative:
                    selected_behavior = behavior
                    break
            
            simulators.append(UserSimulator(i, selected_behavior))
        
        return simulators
    
    async def _execute_with_ramp_up(self, simulators: List[UserSimulator], config: LoadTestConfig) -> List[Dict[str, Any]]:
        """Execute load test with gradual ramp-up of users."""
        all_results = []
        
        # Calculate ramp-up batches
        batch_size = max(1, config.concurrent_users // 5)  # Ramp up in 5 batches
        ramp_up_delay = config.ramp_up_time_seconds / 5
        
        active_tasks = []
        
        for batch_start in range(0, config.concurrent_users, batch_size):
            batch_end = min(batch_start + batch_size, config.concurrent_users)
            batch_simulators = simulators[batch_start:batch_end]
            
            # Start batch of users
            for simulator in batch_simulators:
                if config.test_duration_seconds > 0:
                    task = asyncio.create_task(
                        simulator.simulate_browsing_behavior(config.test_duration_seconds)
                    )
                else:
                    task = asyncio.create_task(
                        simulator.simulate_full_user_journey()
                    )
                active_tasks.append(task)
            
            print(f"Started {len(batch_simulators)} users (total: {batch_end}/{config.concurrent_users})")
            
            # Wait before starting next batch
            if batch_end < config.concurrent_users:
                await asyncio.sleep(ramp_up_delay)
        
        # Wait for all users to complete
        print("Waiting for all users to complete...")
        batch_results = await asyncio.gather(*active_tasks, return_exceptions=True)
        
        # Collect all results
        for result in batch_results:
            if isinstance(result, list):
                all_results.extend(result)
        
        return all_results
    
    def _start_system_monitoring(self):
        """Start monitoring system resources."""
        self.monitoring_active = True
        self.cpu_usage_samples = []
        self.memory_usage_samples = []
        
        def monitor():
            while self.monitoring_active:
                try:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory_info = psutil.virtual_memory()
                    
                    self.cpu_usage_samples.append(cpu_percent)
                    self.memory_usage_samples.append(memory_info.used / 1024 / 1024)  # MB
                except Exception:
                    pass  # Ignore monitoring errors
        
        self.system_monitor = threading.Thread(target=monitor, daemon=True)
        self.system_monitor.start()
    
    def _stop_system_monitoring(self):
        """Stop monitoring system resources."""
        self.monitoring_active = False
        if self.system_monitor:
            self.system_monitor.join(timeout=2)
    
    def _analyze_results(self, all_results: List[Dict[str, Any]], config: LoadTestConfig) -> LoadTestResult:
        """Analyze load test results and generate summary."""
        if not all_results:
            return LoadTestResult(
                total_requests=0, successful_requests=0, failed_requests=0,
                average_response_time=0, median_response_time=0,
                p95_response_time=0, p99_response_time=0, max_response_time=0,
                requests_per_second=0, error_rate=1.0,
                peak_memory_usage_mb=0, cpu_usage_percent=0, test_duration=0
            )
        
        # Filter successful requests for timing analysis
        successful_requests = [r for r in all_results if r['success']]
        failed_requests = [r for r in all_results if not r['success']]
        
        # Calculate timing statistics
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            response_times.sort()
            
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_index = int(len(response_times) * 0.95)
            p99_index = int(len(response_times) * 0.99)
            p95_response_time = response_times[p95_index] if p95_index < len(response_times) else response_times[-1]
            p99_response_time = response_times[p99_index] if p99_index < len(response_times) else response_times[-1]
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = max_response_time = 0
        
        # Calculate rates and usage
        total_requests = len(all_results)
        test_duration = config.test_duration_seconds if config.test_duration_seconds > 0 else 60  # Default estimate
        requests_per_second = total_requests / test_duration if test_duration > 0 else 0
        error_rate = len(failed_requests) / total_requests if total_requests > 0 else 0
        
        # System resource usage
        peak_memory_mb = max(self.memory_usage_samples) if self.memory_usage_samples else 0
        avg_cpu_percent = statistics.mean(self.cpu_usage_samples) if self.cpu_usage_samples else 0
        
        return LoadTestResult(
            total_requests=total_requests,
            successful_requests=len(successful_requests),
            failed_requests=len(failed_requests),
            average_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            peak_memory_usage_mb=peak_memory_mb,
            cpu_usage_percent=avg_cpu_percent,
            test_duration=test_duration
        )


class TestConcurrentUserSimulation:
    """Test system performance with concurrent user simulations."""
    
    def setup_method(self):
        """Set up load testing environment."""
        self.orchestrator = LoadTestOrchestrator()
    
    @pytest.mark.asyncio
    async def test_light_load_simulation(self):
        """Test system performance under light load (10 concurrent users)."""
        config = LoadTestConfig(
            concurrent_users=10,
            test_duration_seconds=30,
            ramp_up_time_seconds=5,
            user_behavior_pattern=UserBehaviorPattern.TYPICAL_USER,
            target_throughput_requests_per_second=20.0,
            max_acceptable_response_time=2.0,
            max_acceptable_error_rate=0.05
        )
        
        result = await self.orchestrator.run_load_test(config)
        
        # Verify performance under light load
        assert result.error_rate <= config.max_acceptable_error_rate, \
            f"Error rate {result.error_rate:.3f} exceeds threshold {config.max_acceptable_error_rate}"
        
        assert result.average_response_time <= config.max_acceptable_response_time, \
            f"Average response time {result.average_response_time:.3f}s exceeds threshold {config.max_acceptable_response_time}s"
        
        assert result.requests_per_second >= config.target_throughput_requests_per_second * 0.8, \
            f"Throughput {result.requests_per_second:.1f} RPS below 80% of target {config.target_throughput_requests_per_second}"
        
        print(f"Light load test results: {result.total_requests} requests, "
              f"{result.average_response_time:.3f}s avg response time, "
              f"{result.error_rate:.3f} error rate")
    
    @pytest.mark.asyncio
    async def test_moderate_load_simulation(self):
        """Test system performance under moderate load (25 concurrent users)."""
        config = LoadTestConfig(
            concurrent_users=25,
            test_duration_seconds=45,
            ramp_up_time_seconds=10,
            user_behavior_pattern=UserBehaviorPattern.TYPICAL_USER,
            target_throughput_requests_per_second=40.0,
            max_acceptable_response_time=3.0,
            max_acceptable_error_rate=0.08
        )
        
        result = await self.orchestrator.run_load_test(config)
        
        # Verify performance under moderate load
        assert result.error_rate <= config.max_acceptable_error_rate, \
            f"Error rate {result.error_rate:.3f} exceeds threshold {config.max_acceptable_error_rate}"
        
        assert result.p95_response_time <= config.max_acceptable_response_time * 1.5, \
            f"P95 response time {result.p95_response_time:.3f}s exceeds threshold"
        
        assert result.successful_requests >= result.total_requests * 0.9, \
            f"Too many failed requests: {result.failed_requests}/{result.total_requests}"
        
        print(f"Moderate load test results: {result.total_requests} requests, "
              f"{result.p95_response_time:.3f}s P95 response time, "
              f"{result.error_rate:.3f} error rate")
    
    @pytest.mark.asyncio
    async def test_heavy_load_simulation(self):
        """Test system performance under heavy load (50 concurrent users)."""
        config = LoadTestConfig(
            concurrent_users=50,
            test_duration_seconds=60,
            ramp_up_time_seconds=15,
            user_behavior_pattern=UserBehaviorPattern.TYPICAL_USER,
            target_throughput_requests_per_second=60.0,
            max_acceptable_response_time=5.0,
            max_acceptable_error_rate=0.10
        )
        
        result = await self.orchestrator.run_load_test(config)
        
        # Verify system doesn't break under heavy load
        assert result.error_rate <= config.max_acceptable_error_rate, \
            f"Error rate {result.error_rate:.3f} exceeds threshold {config.max_acceptable_error_rate}"
        
        assert result.max_response_time <= config.max_acceptable_response_time * 2, \
            f"Maximum response time {result.max_response_time:.3f}s too high"
        
        # System should handle at least 70% of target throughput under heavy load
        assert result.requests_per_second >= config.target_throughput_requests_per_second * 0.7, \
            f"Throughput {result.requests_per_second:.1f} RPS too low for heavy load"
        
        print(f"Heavy load test results: {result.total_requests} requests, "
              f"{result.max_response_time:.3f}s max response time, "
              f"{result.error_rate:.3f} error rate")
    
    @pytest.mark.asyncio
    async def test_mixed_user_behavior_patterns(self):
        """Test system with different user behavior patterns simultaneously."""
        # Create custom orchestrator with mixed patterns
        orchestrator = LoadTestOrchestrator()
        
        # Create users with different behavior patterns
        simulators = [
            UserSimulator(1, UserBehaviorPattern.QUICK_BROWSER),
            UserSimulator(2, UserBehaviorPattern.QUICK_BROWSER),
            UserSimulator(3, UserBehaviorPattern.TYPICAL_USER),
            UserSimulator(4, UserBehaviorPattern.TYPICAL_USER),
            UserSimulator(5, UserBehaviorPattern.TYPICAL_USER),
            UserSimulator(6, UserBehaviorPattern.THOROUGH_USER),
            UserSimulator(7, UserBehaviorPattern.POWER_USER)
        ]
        
        # Run simulations concurrently
        tasks = [simulator.simulate_full_user_journey() for simulator in simulators]
        all_results = await asyncio.gather(*tasks)
        
        # Flatten results
        flattened_results = []
        for result_list in all_results:
            flattened_results.extend(result_list)
        
        # Analyze by behavior pattern
        pattern_stats = {}
        for simulator in simulators:
            pattern = simulator.behavior_pattern.value
            if pattern not in pattern_stats:
                pattern_stats[pattern] = []
            
            user_results = [r for r in flattened_results if r['user_id'] == simulator.user_id and r['success']]
            if user_results:
                avg_response_time = statistics.mean([r['response_time'] for r in user_results])
                pattern_stats[pattern].append(avg_response_time)
        
        # Verify behavior patterns show expected performance characteristics
        if 'quick_browser' in pattern_stats and pattern_stats['quick_browser']:
            quick_avg = statistics.mean(pattern_stats['quick_browser'])
            assert quick_avg < 0.5, f"Quick browsers should be fast: {quick_avg:.3f}s average"
        
        if 'thorough_user' in pattern_stats and pattern_stats['thorough_user']:
            thorough_avg = statistics.mean(pattern_stats['thorough_user'])
            # Thorough users take more time between requests, but API responses should still be fast
            assert thorough_avg < 1.0, f"Thorough users API responses too slow: {thorough_avg:.3f}s average"
        
        print(f"Mixed behavior test: {len(flattened_results)} total requests across {len(simulators)} users")
    
    @pytest.mark.asyncio
    async def test_sustained_load_endurance(self):
        """Test system stability under sustained load over extended period."""
        config = LoadTestConfig(
            concurrent_users=20,
            test_duration_seconds=120,  # 2 minutes of sustained load
            ramp_up_time_seconds=20,
            user_behavior_pattern=UserBehaviorPattern.TYPICAL_USER,
            target_throughput_requests_per_second=30.0,
            max_acceptable_response_time=3.0,
            max_acceptable_error_rate=0.05
        )
        
        result = await self.orchestrator.run_load_test(config)
        
        # Verify system maintains stability over time
        assert result.error_rate <= config.max_acceptable_error_rate, \
            f"Error rate {result.error_rate:.3f} too high for sustained load"
        
        assert result.p99_response_time <= config.max_acceptable_response_time * 2, \
            f"P99 response time {result.p99_response_time:.3f}s indicates performance degradation"
        
        # Check for memory leaks or resource issues
        assert result.peak_memory_usage_mb < 500, \
            f"Memory usage {result.peak_memory_usage_mb:.1f}MB too high for sustained load"
        
        print(f"Sustained load test: {result.test_duration}s duration, "
              f"{result.peak_memory_usage_mb:.1f}MB peak memory, "
              f"{result.cpu_usage_percent:.1f}% avg CPU")
    
    @pytest.mark.asyncio
    async def test_stress_test_capacity_limits(self):
        """Test system behavior at capacity limits (stress test)."""
        config = LoadTestConfig(
            concurrent_users=100,  # High user count to stress the system
            test_duration_seconds=30,  # Shorter duration for stress test
            ramp_up_time_seconds=5,   # Fast ramp-up to stress
            user_behavior_pattern=UserBehaviorPattern.POWER_USER,
            target_throughput_requests_per_second=100.0,
            max_acceptable_response_time=10.0,  # More lenient for stress test
            max_acceptable_error_rate=0.20      # Higher error tolerance
        )
        
        result = await self.orchestrator.run_load_test(config)
        
        # System should not completely fail under stress
        assert result.successful_requests > 0, "System completely failed under stress"
        assert result.error_rate <= config.max_acceptable_error_rate, \
            f"Error rate {result.error_rate:.3f} too high even for stress test"
        
        # System should handle at least 50% of requests successfully under stress
        success_rate = result.successful_requests / result.total_requests
        assert success_rate >= 0.5, f"Success rate {success_rate:.3f} too low for stress test"
        
        print(f"Stress test results: {result.total_requests} requests, "
              f"{success_rate:.3f} success rate, "
              f"{result.requests_per_second:.1f} RPS achieved")


class TestUserJourneyLoadTesting:
    """Test complete user journeys under load."""
    
    @pytest.mark.asyncio
    async def test_full_onboarding_journey_load(self):
        """Test multiple users completing full onboarding journey simultaneously."""
        concurrent_journeys = 15
        
        # Create simulators for full journey
        simulators = [
            UserSimulator(i, UserBehaviorPattern.TYPICAL_USER)
            for i in range(concurrent_journeys)
        ]
        
        # Execute all journeys concurrently
        start_time = time.perf_counter()
        tasks = [simulator.simulate_full_user_journey() for simulator in simulators]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.perf_counter() - start_time
        
        # Analyze journey completion
        completed_journeys = 0
        total_requests = 0
        successful_requests = 0
        
        for i, result in enumerate(all_results):
            if isinstance(result, list):
                user_requests = result
                total_requests += len(user_requests)
                successful_requests += len([r for r in user_requests if r['success']])
                
                # Check if user completed key onboarding steps
                endpoints_hit = set(r['endpoint'] for r in user_requests if r['success'])
                required_endpoints = {'signup', 'language_set', 'industry_set'}
                
                if required_endpoints.issubset(endpoints_hit):
                    completed_journeys += 1
        
        # Verify journey completion rates
        completion_rate = completed_journeys / concurrent_journeys
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        assert completion_rate >= 0.8, \
            f"Only {completed_journeys}/{concurrent_journeys} users completed onboarding ({completion_rate:.2f})"
        
        assert success_rate >= 0.9, \
            f"Request success rate too low: {success_rate:.3f}"
        
        assert total_time < 60, \
            f"Total time for {concurrent_journeys} concurrent journeys too high: {total_time:.1f}s"
        
        print(f"Journey load test: {completed_journeys}/{concurrent_journeys} completed, "
              f"{success_rate:.3f} success rate, {total_time:.1f}s total time")