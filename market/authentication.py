from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.lower().startswith("token "):
            return None
        api_key = auth_header.split(" ", 1)[1]
        try:
            user = User.objects.get(api_key=api_key)
        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid API Key')
        return (user, None)

    def authenticate_header(self, request):
        return 'Token'
