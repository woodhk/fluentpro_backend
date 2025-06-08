"""
Test to verify domain independence and proper isolation.
This test ensures that domains can be tested without cross-domain dependencies.
"""

import pytest
import ast
import os
from pathlib import Path


class TestDomainIndependence:
    """Verify that domains are properly isolated and can be tested independently."""
    
    def test_authentication_domain_isolation(self):
        """Verify authentication domain doesn't import from other domains except shared."""
        auth_domain_path = Path("domains/authentication")
        violations = self._check_domain_imports(auth_domain_path, "authentication")
        
        assert len(violations) == 0, (
            f"Authentication domain has cross-domain dependencies:\n" + 
            "\n".join(violations)
        )
    
    def test_onboarding_domain_isolation(self):
        """Verify onboarding domain doesn't import from other domains except shared."""
        onboarding_domain_path = Path("domains/onboarding")
        violations = self._check_domain_imports(onboarding_domain_path, "onboarding")
        
        assert len(violations) == 0, (
            f"Onboarding domain has cross-domain dependencies:\n" + 
            "\n".join(violations)
        )
    
    def test_domain_tests_use_mocks(self):
        """Verify domain tests use mocks instead of real implementations."""
        test_paths = [
            Path("tests/unit/domains/authentication"),
            Path("tests/unit/domains/onboarding")
        ]
        
        violations = []
        for test_path in test_paths:
            if test_path.exists():
                for py_file in test_path.rglob("*.py"):
                    if py_file.name == "__init__.py":
                        continue
                    
                    content = py_file.read_text()
                    
                    # Check for infrastructure imports
                    if "infrastructure.external_services" in content:
                        violations.append(f"{py_file}: imports real external services")
                    if "infrastructure.persistence" in content:
                        violations.append(f"{py_file}: imports real persistence layer")
                    
                    # Check for direct database/API imports
                    if "supabase" in content.lower() and "mock" not in content.lower():
                        violations.append(f"{py_file}: may use real Supabase client")
                    if "auth0" in content.lower() and "mock" not in content.lower():
                        violations.append(f"{py_file}: may use real Auth0 client")
        
        assert len(violations) == 0, (
            f"Domain tests have infrastructure dependencies:\n" + 
            "\n".join(violations)
        )
    
    def test_test_fixtures_are_domain_specific(self):
        """Verify each domain has its own test fixtures."""
        required_fixtures = {
            "tests/unit/domains/authentication/conftest.py": [
                "mock_user_repository",
                "mock_role_repository",
                "mock_auth_service"
            ],
            "tests/unit/domains/onboarding/conftest.py": [
                "mock_industry_repository",
                "mock_partner_repository",
                "mock_embedding_service"
            ]
        }
        
        for fixture_file, expected_fixtures in required_fixtures.items():
            fixture_path = Path(fixture_file)
            assert fixture_path.exists(), f"Missing fixture file: {fixture_file}"
            
            content = fixture_path.read_text()
            for fixture in expected_fixtures:
                assert f"def {fixture}" in content, (
                    f"Missing fixture '{fixture}' in {fixture_file}"
                )
    
    def test_no_circular_dependencies(self):
        """Verify there are no circular dependencies between domains."""
        # Check that authentication doesn't import from onboarding
        auth_imports = self._get_all_imports(Path("domains/authentication"))
        assert not any("domains.onboarding" in imp for imp in auth_imports), (
            "Authentication domain imports from onboarding domain"
        )
        
        # Check that onboarding doesn't import from authentication (except interfaces)
        onboarding_imports = self._get_all_imports(Path("domains/onboarding"))
        auth_imports_in_onboarding = [
            imp for imp in onboarding_imports 
            if "domains.authentication" in imp and "interfaces" not in imp
        ]
        
        assert len(auth_imports_in_onboarding) == 0, (
            f"Onboarding domain has non-interface imports from authentication:\n" +
            "\n".join(auth_imports_in_onboarding)
        )
    
    def _check_domain_imports(self, domain_path: Path, domain_name: str) -> list:
        """Check for cross-domain imports in a given domain."""
        violations = []
        
        if not domain_path.exists():
            return violations
        
        for py_file in domain_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if self._is_cross_domain_import(alias.name, domain_name):
                                violations.append(
                                    f"{py_file.relative_to('.')}: imports {alias.name}"
                                )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and self._is_cross_domain_import(node.module, domain_name):
                            violations.append(
                                f"{py_file.relative_to('.')}: imports from {node.module}"
                            )
            except Exception as e:
                violations.append(f"{py_file}: Error parsing file - {str(e)}")
        
        return violations
    
    def _is_cross_domain_import(self, import_path: str, current_domain: str) -> bool:
        """Check if an import is a cross-domain import."""
        # Allow shared domain imports
        if "domains.shared" in import_path:
            return False
        
        # Allow imports from same domain
        if f"domains.{current_domain}" in import_path:
            return False
        
        # Check if it's importing from another domain
        other_domains = ["authentication", "onboarding"]
        other_domains.remove(current_domain)
        
        for other_domain in other_domains:
            if f"domains.{other_domain}" in import_path:
                return True
        
        return False
    
    def _get_all_imports(self, domain_path: Path) -> list:
        """Get all imports from a domain."""
        imports = []
        
        if not domain_path.exists():
            return imports
        
        for py_file in domain_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.append(node.module)
            except:
                pass
        
        return imports


@pytest.mark.asyncio
async def test_authentication_use_case_runs_with_mocks():
    """Verify authentication use case can run with only mocked dependencies."""
    from tests.unit.domains.authentication.conftest import (
        mock_user_repository, mock_auth_service
    )
    from domains.authentication.use_cases.register_user import RegisterUserUseCase
    from domains.authentication.dto.requests import SignupRequest
    
    # Create mocks
    user_repo = mock_user_repository()
    auth_service = mock_auth_service()
    
    # Mock the authenticate method
    auth_service.authenticate = lambda email, password: {
        "access_token": "test-token",
        "refresh_token": "test-refresh",
        "expires_in": 3600
    }
    
    # Create use case with mocks
    use_case = RegisterUserUseCase(
        auth_service=auth_service,
        user_repository=user_repo
    )
    
    # Execute use case
    request = SignupRequest(
        email="isolated@test.com",
        password="TestPass123!",
        full_name="Isolated Test"
    )
    
    response = await use_case.execute(request)
    
    # Verify it works
    assert response.user.email == "isolated@test.com"
    assert response.tokens.access_token == "test-token"


@pytest.mark.asyncio
async def test_onboarding_use_case_runs_with_mocks():
    """Verify onboarding use case can run with only mocked dependencies."""
    from tests.unit.domains.onboarding.conftest import (
        mock_user_repository, mock_industry_repository
    )
    from domains.onboarding.use_cases.select_user_industry import SelectUserIndustryUseCase
    from domains.onboarding.dto.requests import SelectIndustryRequest
    from domains.authentication.models.user import User, UserProfile
    
    # Create mocks
    user_repo = mock_user_repository() 
    industry_repo = mock_industry_repository()
    
    # Setup test data
    user = User(
        id="test-user",
        email="test@example.com",
        full_name="Test User",
        auth0_id="auth0|test"
    )
    await user_repo.save(user)
    
    # Create use case with mocks
    use_case = SelectUserIndustryUseCase(
        user_repository=user_repo,
        industry_repository=industry_repo
    )
    
    # Execute use case
    request = SelectIndustryRequest(
        user_id="test-user",
        industry_id="1"
    )
    
    response = await use_case.execute(request)
    
    # Verify it works
    assert response.success is True
    assert response.industry_name == "Technology"