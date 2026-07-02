# APP
class AppExceptionError(Exception):
    def __init__(self, message, status_code: int):
        self.message = message
        self.status_code = status_code


class DataIntegrityError(AppExceptionError):
    def __init__(self, message: str = "App data integrity error."):
        super().__init__(message, status_code=400)


# AUTH
class AuthenticationError(AppExceptionError):
    def __init__(self, message: str = "Incorrect email or password."):
        super().__init__(message, status_code=401)


class AuthorizationError(AppExceptionError):
    def __init__(self, message: str = "Not allowed to access the resource."):
        super().__init__(message, status_code=403)


class TokenExpiredError(AppExceptionError):
    def __init__(self, message: str = "Session expired."):
        super().__init__(message, status_code=401)


class InvalidTokenSignatureError(AppExceptionError):
    def __init__(self, message: str = "Token signature doesn't match."):
        super().__init__(message, status_code=403)


class TokenDecodingError(AppExceptionError):
    def __init__(self, message: str = "Malformed or invalid token."):
        super().__init__(message, status_code=422)


# AWS
class S3StorageError(AppExceptionError):
    def __init__(self, message: str = "Cloud storage pipeline rejected file upload."):
        super().__init__(message, status_code=424)


# DATABASE
class DatabaseError(AppExceptionError):
    def __init__(self, message: str = "Database failed to complete the task."):
        super().__init__(message, status_code=500)


class EntryNotFoundError(AppExceptionError):
    def __init__(self, message: str = "Database could not find the entry."):
        super().__init__(message, status_code=404)


class DatabaseIntegrityError(AppExceptionError):
    def __init__(self, message: str = "Database integrity error."):
        super().__init__(message, status_code=409)


class DocumentUploadError(AppExceptionError):
    def __init__(
        self, message: str = "Document registration sequence failed completely."
    ):
        super().__init__(message, status_code=500)
