from enum import Enum


class NativeLanguage(str, Enum):
    ENGLISH = "english"
    CHINESE_TRADITIONAL = "chinese_traditional"
    CHINESE_SIMPLIFIED = "chinese_simplified"


class OnboardingStatus(str, Enum):
    PENDING = "pending"
    WELCOME = "welcome"
    BASIC_INFO = "basic_info"
    PERSONALISATION = "personalisation"
    COMPLETED = "completed"


class HierarchyLevel(str, Enum):
    ASSOCIATE = "associate"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    DIRECTOR = "director"