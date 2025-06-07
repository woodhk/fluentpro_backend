from application.exceptions.base_exceptions import ApplicationException

class InfrastructureException(ApplicationException):
    """Base for all infrastructure exceptions"""
    status_code = 503

class ExternalServiceException(InfrastructureException):
    """External service call failed"""
    pass

class DatabaseException(InfrastructureException):
    """Database operation failed"""
    pass