from django.conf.urls import url, patterns

urlpatterns = patterns('payment.views',
    url(r'^logs/$', 'logs', {'template_name': 'payment/logs.html'}), 
    url(r'^account_list/$', 'account_list'),
    url(r'^account_deposite/(?P<user_id>\d+)/$', 'account_deposite'),
    url(r'^account_deposite_done/$', 'account_deposite_done'),
)