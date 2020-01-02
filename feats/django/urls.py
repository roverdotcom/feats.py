from django.conf.urls import url

from . import views

app_name = 'feats'
urlpatterns = [
    url(r'^([^/]+)/selectors/$', views.AddSelector.as_view(), name='add-selector')
    url(r'^([^/]+)/selectors/([^/]+)/$', views.ChangeSelector.as_view(), name='update-selector'),
    url(r'^([^/]+)/segmentation/$', views.ChangeSegmentation.as_view(), name='feature-segmentation'),
    url(r'^([^/]+)/$', views.Detail.as_view(), name='detail'),
    url(r'^$', views.Index.as_view(), name='index'),
]
