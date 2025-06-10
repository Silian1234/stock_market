from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "").strip()
        if auth_header.lower().startswith("token "):
            api_key = auth_header.split(" ", 1)[1]
        else:
            api_key = auth_header
        if not api_key:
            return None
        try:
            user = User.objects.get(api_key=api_key)
        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid API Key')
        return (user, None)

    def authenticate_header(self, request):
        return 'Token'
