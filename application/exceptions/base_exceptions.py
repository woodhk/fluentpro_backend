class ApplicationException(Exception):
    """Base exception for all application errors"""
    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.code = code