from django.urls import path

from . import views

urlpatterns = [
        path('', views.Index.as_view(), name='index'),
        path('<name>', views.Detail.as_view(), name='detail'),
        path('<name>/edit', views.Change.as_view(), name='update'),
]
