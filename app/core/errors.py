class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def bad_request(message: str, code: str = "validation_error") -> APIError:
    return APIError(400, code, message)


def unauthorized(message: str = "Authentication required.", code: str = "authentication_required") -> APIError:
    return APIError(401, code, message)


def forbidden(message: str = "You do not have access to this resource.", code: str = "authorization_denied") -> APIError:
    return APIError(403, code, message)


def not_found(message: str, code: str = "resource_not_found") -> APIError:
    return APIError(404, code, message)


def conflict(message: str, code: str = "conflict") -> APIError:
    return APIError(409, code, message)


def upstream_failure(message: str = "Upstream AI service failed.", code: str = "upstream_ai_failure") -> APIError:
    return APIError(502, code, message)
