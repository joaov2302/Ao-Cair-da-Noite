from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/session', views.session), path('api/auth/<str:action>', views.auth),
    path('api/campaigns', views.campaigns), path('api/campaigns/<int:pk>/rules', views.catalog),
    path('api/campaigns/<int:pk>/invites', views.invites), path('api/campaigns/<int:pk>/decisions', views.decision),
    path('api/join', views.join), path('api/characters', views.characters),
    path('api/characters/preview', views.preview), path('api/comparisons', views.comparisons),
    path('api/characters/<uuid:pk>', views.character_detail), path('api/characters/<uuid:pk>/submissions', views.submit),
    path('api/submissions/<int:pk>/reviews', views.reviews), path('api/characters/<uuid:pk>/resources', views.resources),
    path('api/characters/<uuid:pk>/export', views.export), path('api/assets/<int:pk>/content', views.asset_content),
    path('api/rolls', views.roll),
]
