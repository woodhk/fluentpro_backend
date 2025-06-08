"""
Test data generators for creating realistic test data.
"""

import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from faker import Faker


fake = Faker()


class TestDataGenerator:
    """Generates realistic test data for various entities."""
    
    INDUSTRIES = [
        "Technology", "Healthcare", "Finance", "Education", "Manufacturing",
        "Retail", "Consulting", "Media", "Transportation", "Real Estate"
    ]
    
    ROLES_BY_INDUSTRY = {
        "Technology": [
            "Software Engineer", "Product Manager", "DevOps Engineer", 
            "Data Scientist", "UI/UX Designer", "Technical Lead"
        ],
        "Healthcare": [
            "Physician", "Nurse", "Medical Assistant", "Hospital Administrator",
            "Pharmacist", "Medical Technician"
        ],
        "Finance": [
            "Financial Analyst", "Investment Banker", "Accountant",
            "Risk Manager", "Compliance Officer", "Portfolio Manager"
        ],
        "Education": [
            "Teacher", "Principal", "Academic Counselor", "Curriculum Designer",
            "Educational Administrator", "Research Assistant"
        ]
    }
    
    COMMUNICATION_PARTNERS = [
        "Senior Management", "Direct Reports", "Customers", "Colleagues",
        "External Partners", "Vendors", "Board Members", "Investors"
    ]
    
    COMMUNICATION_UNITS = [
        "Meetings", "Presentations", "Phone Calls", "Emails", "Video Conferences",
        "Team Briefings", "Client Demos", "Training Sessions", "Interviews"
    ]
    
    @staticmethod
    def generate_user_data(include_profile: bool = True) -> Dict[str, Any]:
        """Generate realistic user data."""
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}"
        
        user_data = {
            'id': str(uuid.uuid4()),
            'email': email,
            'full_name': f"{first_name} {last_name}",
            'auth0_id': f"auth0|{uuid.uuid4()}",
            'is_active': random.choice([True, True, True, False]),  # 75% active
            'onboarding_status': random.choice(['pending', 'in_progress', 'completed']),
            'created_at': fake.date_time_between(start_date='-1y', end_date='now'),
            'updated_at': fake.date_time_between(start_date='-30d', end_date='now')
        }
        
        if include_profile:
            user_data['profile'] = TestDataGenerator.generate_profile_data(user_data['id'])
        
        return user_data
    
    @staticmethod
    def generate_profile_data(user_id: str) -> Dict[str, Any]:
        """Generate realistic user profile data."""
        return {
            'user_id': user_id,
            'bio': fake.text(max_nb_chars=200),
            'avatar_url': f"https://example.com/avatars/{uuid.uuid4()}.jpg",
            'preferred_language': random.choice(['en', 'es', 'fr', 'de', 'zh']),
            'timezone': fake.timezone(),
            'locale': random.choice(['en_US', 'es_ES', 'fr_FR', 'de_DE', 'zh_CN']),
            'phone_number': fake.phone_number(),
            'company': fake.company(),
            'department': random.choice(['Engineering', 'Sales', 'Marketing', 'HR', 'Finance']),
            'job_title': fake.job(),
            'years_experience': random.randint(0, 30),
            'education_level': random.choice(['High School', 'Bachelor', 'Master', 'PhD']),
            'linkedin_url': f"https://linkedin.com/in/{fake.user_name()}",
            'github_url': f"https://github.com/{fake.user_name()}"
        }
    
    @staticmethod
    def generate_role_data(industry: Optional[str] = None) -> Dict[str, Any]:
        """Generate realistic role data."""
        if not industry:
            industry = random.choice(TestDataGenerator.INDUSTRIES)
        
        roles = TestDataGenerator.ROLES_BY_INDUSTRY.get(
            industry, 
            TestDataGenerator.ROLES_BY_INDUSTRY["Technology"]
        )
        title = random.choice(roles)
        
        return {
            'id': str(uuid.uuid4()),
            'title': title,
            'description': f"Responsible for {fake.text(max_nb_chars=150)}",
            'industry_id': industry.lower().replace(' ', '_'),
            'hierarchy_level': random.choice(['executive', 'manager', 'individual_contributor']),
            'is_active': random.choice([True, True, True, False]),  # 75% active
            'required_skills': [fake.word() for _ in range(random.randint(3, 7))],
            'experience_level': random.choice(['entry', 'mid', 'senior', 'lead']),
            'salary_range': {
                'min': random.randint(40000, 80000),
                'max': random.randint(90000, 200000),
                'currency': 'USD'
            },
            'remote_work': random.choice([True, False]),
            'location': fake.city(),
            'created_at': fake.date_time_between(start_date='-2y', end_date='now'),
            'updated_at': fake.date_time_between(start_date='-30d', end_date='now')
        }
    
    @staticmethod
    def generate_industry_data() -> Dict[str, Any]:
        """Generate realistic industry data."""
        industry_name = random.choice(TestDataGenerator.INDUSTRIES)
        return {
            'id': str(uuid.uuid4()),
            'name': industry_name,
            'description': f"The {industry_name.lower()} industry encompasses {fake.text(max_nb_chars=100)}",
            'role_count': random.randint(10, 100),
            'is_active': True,
            'growth_rate': round(random.uniform(-5.0, 15.0), 2),
            'average_salary': random.randint(50000, 150000),
            'created_at': fake.date_time_between(start_date='-5y', end_date='-1y'),
            'updated_at': fake.date_time_between(start_date='-30d', end_date='now')
        }
    
    @staticmethod
    def generate_communication_partner_data() -> Dict[str, Any]:
        """Generate realistic communication partner data."""
        partner_name = random.choice(TestDataGenerator.COMMUNICATION_PARTNERS)
        return {
            'id': str(uuid.uuid4()),
            'name': partner_name,
            'description': f"Communication with {partner_name.lower()} involves {fake.text(max_nb_chars=100)}",
            'is_active': True,
            'frequency': random.choice(['daily', 'weekly', 'monthly', 'quarterly']),
            'importance_level': random.choice(['low', 'medium', 'high', 'critical']),
            'created_at': fake.date_time_between(start_date='-1y', end_date='now')
        }
    
    @staticmethod
    def generate_communication_unit_data() -> Dict[str, Any]:
        """Generate realistic communication unit data."""
        unit_name = random.choice(TestDataGenerator.COMMUNICATION_UNITS)
        return {
            'id': str(uuid.uuid4()),
            'name': unit_name,
            'description': f"{unit_name} are used for {fake.text(max_nb_chars=80)}",
            'is_active': True,
            'duration_minutes': random.randint(15, 120),
            'formality_level': random.choice(['casual', 'business', 'formal']),
            'participant_count': random.randint(2, 20),
            'created_at': fake.date_time_between(start_date='-1y', end_date='now')
        }
    
    @staticmethod
    def generate_onboarding_session_data(user_id: str) -> Dict[str, Any]:
        """Generate realistic onboarding session data."""
        started_at = fake.date_time_between(start_date='-30d', end_date='now')
        
        return {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'status': random.choice(['started', 'in_progress', 'completed', 'abandoned']),
            'current_step': random.choice([
                'language_selection', 'industry_selection', 'role_matching',
                'partner_selection', 'communication_setup', 'finalization'
            ]),
            'started_at': started_at,
            'completed_at': fake.date_time_between(
                start_date=started_at, 
                end_date='now'
            ) if random.choice([True, False]) else None,
            'progress_percentage': random.randint(0, 100),
            'selected_language': random.choice(['en', 'es', 'fr', 'de', 'zh']),
            'selected_industry_id': str(uuid.uuid4()),
            'matched_role_id': str(uuid.uuid4()) if random.choice([True, False]) else None,
            'custom_role_description': fake.text(max_nb_chars=150) if random.choice([True, False]) else None,
            'communication_preferences': {
                'partners': random.sample(TestDataGenerator.COMMUNICATION_PARTNERS, k=random.randint(2, 5)),
                'units': random.sample(TestDataGenerator.COMMUNICATION_UNITS, k=random.randint(3, 6)),
                'formality_preference': random.choice(['casual', 'business', 'formal'])
            },
            'created_at': started_at,
            'updated_at': fake.date_time_between(start_date=started_at, end_date='now')
        }
    
    @staticmethod
    def generate_language_proficiency_data(user_id: str) -> Dict[str, Any]:
        """Generate realistic language proficiency data."""
        return {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'language_code': random.choice(['en', 'es', 'fr', 'de', 'zh', 'ja', 'it', 'pt']),
            'language_name': random.choice([
                'English', 'Spanish', 'French', 'German', 
                'Chinese', 'Japanese', 'Italian', 'Portuguese'
            ]),
            'proficiency_level': random.choice(['beginner', 'intermediate', 'advanced', 'fluent', 'native']),
            'is_native': random.choice([True, False]),
            'is_learning': random.choice([True, False]),
            'assessment_score': random.randint(1, 100),
            'assessment_date': fake.date_time_between(start_date='-1y', end_date='now'),
            'goals': [fake.sentence() for _ in range(random.randint(1, 3))],
            'created_at': fake.date_time_between(start_date='-1y', end_date='now'),
            'updated_at': fake.date_time_between(start_date='-30d', end_date='now')
        }


class BulkDataGenerator:
    """Generate bulk test data for performance testing."""
    
    @staticmethod
    def generate_users(count: int) -> List[Dict[str, Any]]:
        """Generate bulk user data."""
        return [TestDataGenerator.generate_user_data() for _ in range(count)]
    
    @staticmethod
    def generate_roles(count: int) -> List[Dict[str, Any]]:
        """Generate bulk role data."""
        return [TestDataGenerator.generate_role_data() for _ in range(count)]
    
    @staticmethod
    def generate_industries(count: int) -> List[Dict[str, Any]]:
        """Generate bulk industry data."""
        return [TestDataGenerator.generate_industry_data() for _ in range(count)]
    
    @staticmethod
    def generate_complete_dataset(
        users: int = 100,
        roles: int = 50,
        industries: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate a complete dataset for comprehensive testing."""
        return {
            'users': BulkDataGenerator.generate_users(users),
            'roles': BulkDataGenerator.generate_roles(roles),
            'industries': BulkDataGenerator.generate_industries(industries),
            'communication_partners': [
                TestDataGenerator.generate_communication_partner_data() 
                for _ in range(20)
            ],
            'communication_units': [
                TestDataGenerator.generate_communication_unit_data() 
                for _ in range(30)
            ]
        }