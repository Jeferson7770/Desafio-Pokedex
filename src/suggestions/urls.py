from rest_framework.routers import DefaultRouter
from ..suggestions.views.suggestions_endpoint import SuggestionViewSet

router = DefaultRouter()
router.register("", SuggestionViewSet, basename="suggestions")

urlpatterns = router.urls