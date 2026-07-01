import threading

# Thread-local storage for request data
_thread_locals = threading.local()


class AuditMiddleware:
    """Middleware to capture request metadata for audit logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request data in thread-local for access from model signals
        _thread_locals.request = request
        _thread_locals.ip_address = self.get_client_ip(request)
        _thread_locals.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        response = self.get_response(request)

        # Clean up thread-local
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request

        return response

    @staticmethod
    def get_client_ip(request):
        """Extract the client's IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


def get_current_request():
    """Get the current request from thread-local storage."""
    return getattr(_thread_locals, 'request', None)


def get_current_ip():
    """Get the current client IP from thread-local storage."""
    return getattr(_thread_locals, 'ip_address', None)


def get_current_user_agent():
    """Get the current user agent from thread-local storage."""
    return getattr(_thread_locals, 'user_agent', '')
