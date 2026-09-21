from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using either their username OR email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
            
        username_or_email = username.strip()
        try:
            user = User.objects.get(
                Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)
            )
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            users = User.objects.filter(
                Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)
            )
            for user in users:
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            return None
            
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
