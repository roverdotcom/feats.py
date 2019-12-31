from django.conf.urls import url

from . import views

app_name = 'feats'
urlpatterns = [
        url(r'^([^/]+)/edit/$', views.Change.as_view(), name='update'),
        url(r'^([^/]+)/$', views.Detail.as_view(), name='detail'),
        url(r'^$', views.Index.as_view(), name='index'),
]
