from rest_framework import routers # type: ignore
from .views import SingleListViewSet, SingleObjectViewSet, PersonViewSet, GroupObjectViewSet, GroupListViewSet, DublettenViewSet, PersonProxyViewSet




router = routers.DefaultRouter()
router.register(r'/groups-list', GroupListViewSet) # type: ignore
router.register(r'/groups-object', GroupObjectViewSet) # type: ignore
router.register(r'/persons', PersonViewSet) # type: ignore
router.register(r'/singles-list', SingleListViewSet) # type: ignore
router.register(r'/singles-object', SingleObjectViewSet) # type: ignore
router.register(r'/dubletten', DublettenViewSet) # type: ignore
router.register(r'/person-proxies', PersonProxyViewSet) # type: ignore
