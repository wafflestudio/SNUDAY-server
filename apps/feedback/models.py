from django.db import models
from apps.user.models import User


class Feedback(models.Model):
    user = models.ForeignKey(
        User,
        related_name="feedback",
        on_delete=models.SET_NULL,
        db_column="user_id",
    )
    content = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
