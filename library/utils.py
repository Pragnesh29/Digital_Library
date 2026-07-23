from .models import AuditLog

def log_action(user, action, details):
    try:
        AuditLog.objects.create(user=user, action=action, details=details)
    except Exception as e:
        # Silently fail or log to python logger in production
        pass
