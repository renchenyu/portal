from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'accounts/login.html'}),
    url(r'^profile/$', 'accounts.views.profile', {'template_name': 'accounts/profile.html'}),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/accounts/login/'}),
    url(r'^password_change/$', 'django.contrib.auth.views.password_change', 
        {'template_name': 'accounts/password_change.html'}),
    url(r'^password_change_done/$', 'django.contrib.auth.views.password_change_done',
        {'template_name': 'accounts/password_change_done.html'}),
)
                       
