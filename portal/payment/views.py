# -*- coding:utf8 -*-

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.template import RequestContext
from django.core.urlresolvers import reverse

from payment.forms import AccountDepositeForm

@login_required
def logs(request, template_name):
    user = request.user
    payment_logs = user.account.log_set.order_by('-datetime')
    return render_to_response(template_name, {'payment_logs': payment_logs})

@login_required
@permission_required('payment.deposite_account', raise_exception=True)
def account_list(request):
    users = User.objects.select_related('account').all()
    return render_to_response('payment/account_list.html', {'users': users})

@login_required
@permission_required('payment.deposite_account', raise_exception=True)
def account_deposite(request, user_id):
    other = None
    try:
        other = User.objects.select_related('account').get(pk=user_id)
    except User.DoesNotExist:
        return HttpResponseNotFound()
    
    if request.method == 'POST':
        form = AccountDepositeForm(request.POST)
        if form.is_valid():
            other.account.deposite(form.cleaned_data['money'], request.user, form.cleaned_data['detail'])
            return HttpResponseRedirect(reverse('payment.views.account_deposite_done'))
    else:
        form = AccountDepositeForm(initial={'user_id': user_id})
        
    return render_to_response('payment/account_deposite.html', {'form': form, 'other': other}, 
                              context_instance=RequestContext(request))

@login_required
@permission_required('payment.deposite_account', raise_exception=True)
def account_deposite_done(request):
    return render_to_response('payment/account_deposite_done.html')