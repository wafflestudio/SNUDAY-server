from rest_framework import routers
from apps.feedback.views import FeedbackView

router = routers.SimpleRouter()
router.register(r"feedback", FeedbackView)
urlpatterns = router.urls
