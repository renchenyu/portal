from django.conf.urls import patterns, url

urlpatterns = patterns('meal.views',
    url(r'^menu/(?P<restaurant_id>\d+)/$', 'menu'),
    url(r'^menu/$', 'menu'),
    url(r'^order/$', 'order'),
    url(r'^list/$', 'summary'),
    url(r'^list/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$', 'summary'),
    url(r'^toggle_lock/$', 'toggle_lock'),
    url(r'^finish/$', 'mark_all_as_finished'),
    url(r'^cancel/(?P<order_id>\d+)/$', 'cancel_order'),
)