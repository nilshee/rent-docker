from django.urls import include, path
from . import views
from rest_framework import routers
from knox import views as knox_views
from api.views import LoginView

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'rentalobjects', views.RentalobjectViewSet)
router.register(r'rentalobjecttypes', views.RentalobjectTypeViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'reservations', views.ReservationViewSet)
router.register(r'tags', views.TagViewSet)
router.register(r'texts', views.TextViewSet)
router.register(r'settings', views.SettingsViewSet)
router.register(r'rentals', views.RentalViewSet)
router.register(r'duration', views.MaxRentDurationViewSet)
router.register(r'priority', views.PriorityViewSet)
router.register(r'files', views.FilesViewSet)
router.register(r'profile', views.ProfileViewSet)
router.register(r'workplace', views.OnPremiseWorkplaceViewSet)
router.register(r'onpremisebooking', views.OnPremiseBookingViewSet)
router.register(r'onpremiseblockedtimes', views.OnPremiseBlockedTimesViewSet)

urlpatterns = [
    path(r'auth/login/', LoginView.as_view(), name='knox_login'),
    path(r'auth/logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path(r'auth/logoutall/', knox_views.LogoutAllView.as_view(),
         name='knox_logoutall'),
    path(r'auth/checkcredentials/', views.checkCredentials,
         name='check credentials return 200 if valid'),
]
urlpatterns += router.urls
