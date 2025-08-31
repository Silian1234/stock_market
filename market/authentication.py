from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "").strip()

        if not auth_header:
            return None

        parts = auth_header.split()
        # The API expects the prefix to be exactly "TOKEN" in upper case.
        if len(parts) != 2 or parts[0] != "TOKEN":
            return None

        api_key = parts[1]
        try:
            user = User.objects.get(api_key=api_key)
        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid API Key')
        return (user, None)

    def authenticate_header(self, request):
        return 'TOKEN'
