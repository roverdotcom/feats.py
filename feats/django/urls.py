from django.conf.urls import url

from . import views

app_name = 'feats'
urlpatterns = [
    url(r'^features/([^/]+)/selectors/$', views.AddSelector.as_view(), name='add-selector'),
    url(r'^features/([^/]+)/selectors/([^/]+)/$', views.ChangeSelector.as_view(), name='update-selector'),
    url(r'^features/([^/]+)/segmentation/$', views.ChangeSegmentation.as_view(), name='update-segmentation'),
    url(r'^features/([^/]+)/segmentation-mapping/$', views.ChangeMapping.as_view(), name='update-mapping'),
    url(r'^features/([^/]+)/$', views.Detail.as_view(), name='detail'),
    url(r'^$', views.Index.as_view(), name='index'),
]
