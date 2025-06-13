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


class Industry(str, Enum):
    BANKING_FINANCE = "banking_finance"
    SHIPPING_LOGISTICS = "shipping_logistics" 
    REAL_ESTATE = "real_estate"
    HOTELS_HOSPITALITY = "hotels_hospitality"


class CommunicationPartnerType(str, Enum):
    CLIENTS = "Clients"
    SENIOR_MANAGEMENT = "Senior Management"
    SUPPLIERS = "Suppliers"
    CUSTOMERS = "Customers"
    COLLEAGUES = "Colleagues"
    STAKEHOLDERS = "Stakeholders"
    PARTNERS = "Partners"


class CommunicationSituation(str, Enum):
    INTERVIEWS = "Interviews"
    CONFLICT_RESOLUTION = "Conflict Resolution"
    PHONE_CALLS = "Phone Calls"
    ONE_ON_ONES = "One-on-Ones"
    FEEDBACK_SESSIONS = "Feedback Sessions"
    TEAM_DISCUSSIONS = "Team Discussions"
    NEGOTIATIONS = "Negotiations"
    STATUS_UPDATES = "Status Updates"
    INFORMAL_CHATS = "Informal Chats"
    BRIEFINGS = "Briefings"
    MEETINGS = "Meetings"
    PRESENTATIONS = "Presentations"
    TRAINING_SESSIONS = "Training Sessions"
    CLIENT_CONVERSATIONS = "Client Conversations"
    VIDEO_CONFERENCES = "Video Conferences"