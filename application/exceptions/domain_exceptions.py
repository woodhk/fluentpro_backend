from application.exceptions.base_exceptions import ApplicationException

class DomainException(ApplicationException):
    """Base for all domain exceptions"""
    status_code = 400

class EntityNotFoundException(DomainException):
    """Entity not found in repository"""
    status_code = 404

class InvalidCredentialsError(DomainException):
    """Invalid authentication credentials"""
    status_code = 401

class BusinessRuleViolationError(DomainException):
    """Business rule violated"""
    status_code = 422

class ValidationException(DomainException):
    """Input validation error"""
    status_code = 400