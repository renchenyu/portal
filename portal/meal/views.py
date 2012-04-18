# -*- coding:utf8 -*-
import itertools
from collections import defaultdict

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound, HttpResponseRedirect, HttpResponseNotAllowed, \
    HttpResponseForbidden
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import transaction

from meal.models import Order, Restaurant, Meal, Lock

def sys_is_unlocked(meth):
    def new(*args, **kwargs):
        if Lock.is_locked():
            return HttpResponseForbidden('订餐系统已经锁定')
        return meth(*args, **kwargs)
    return new


@login_required
def menu(request, restaurant_id=0):
    params = {
        'restaurants': Restaurant.objects.all(),
    }
    
    if not restaurant_id:
        my_orders = request.user.order_by_myself.order_by('-id')
        if my_orders.count() > 0:
            restaurant_id = my_orders[0].meal.restaurant.id
        elif params['restaurants'].count() != 0:
            restaurant_id = params['restaurants'][0].id
    
    if restaurant_id:
        try:
            restaurant = params['restaurant'] = Restaurant.objects.get(pk=restaurant_id)
            params['meals'] = restaurant.meal_set.all()
        except Restaurant.DoesNotExist:
            return HttpResponseNotFound()
        
    params['all_users'] = User.objects.all()

    return render_to_response('meal/menu.html', params, context_instance=RequestContext(request))

@login_required
@sys_is_unlocked
def order(request):
    if request.method == 'POST':
        
        meal_ids = request.POST.getlist('meal_ids')
        meals = Meal.objects.in_bulk(meal_ids)
        
        if len(meals) == 0:
            return HttpResponseRedirect(reverse('meal.views.menu'))
            
        try:
            payer_id = request.POST['payer_id']
            payer = request.user
            if payer_id != payer.id:
                payer = User.objects.get(pk=payer_id)
                
            #TODO: is there good solution for dynamic forms?
            orders = []
            for id, meal in meals.iteritems():
                num = request.POST['num_' + str(id)]
                try:
                    num = int(num)
                except ValueError:
                    num = 1
                if not 0 < num < 1000:
                    num = 1
                    
                orders.append(Order(
                    order_user=payer,
                    for_user=request.user,
                    meal=meal,
                    restaurant=meal.restaurant,
                    num=num,
                ))
                
            Order.objects.bulk_create(orders)
            
            return HttpResponseRedirect(reverse('meal.views.summary'))
                
        except KeyError:
            return HttpResponseRedirect(reverse('meal.views.menu'))
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('meal.views.menu'))
    else:
        return HttpResponseNotAllowed(['POST'])
        
@login_required
def summary(request, year=None, month=None, day=None):
    orders = None
    if year == None and month == None and day == None:
        orders = Order.today()
    else:
        orders = Order.by_date(year, month, day)
    
    orders = orders.select_related('meal', 'restaurant', 'order_for').order_by('restaurant', 'for_user')
  
    # data for unorderd users      
    ordered_user_set = set([order.for_user for order in orders])
    all_user_set = set([user for user in User.objects.all()])
    
    # is meal sys locked?
    locked = Lock.is_locked()
    
    orders_group_by_restaurant = _regroup_and_sum_orders(orders)
        
    return render_to_response('meal/list.html', {'orders': orders,
        'orders_group_by_restaurant': orders_group_by_restaurant,
        'unordered_users': all_user_set - ordered_user_set, 'locked': locked}, 
        context_instance=RequestContext(request))
    
@login_required
@permission_required('meal.change_lock', raise_exception=True)
def toggle_lock(request):
    Lock.toggle()
    return HttpResponseRedirect(reverse('meal.views.summary'))

@login_required
@permission_required('meal.change_lock', raise_exception=True)
@transaction.commit_on_success
def mark_all_as_finished(request):
    orders = Order.objects.select_related('meal', 'restaurant').select_for_update().filter(state=0)
    for order in orders:
        detail = "{restaurant_name} | {meal_name} * {num} | {price}".format(
            restaurant_name=order.restaurant.name,
            meal_name=order.meal.name,
            num=order.num,
            price=order.meal.price_today()                                                                    
        )
        order.for_user.account.withdraw(order.meal.price_today() * order.num, detail)
        order.state = 1
        order.save()
        
    return HttpResponseRedirect(reverse('meal.views.summary'))

@login_required
@sys_is_unlocked
def cancel_order(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
        if order.order_user == request.user or order.for_user == request.user:
            order.delete()
    except Order.DoseNotExist:
        pass
        
    return HttpResponseRedirect(reverse('meal.views.summary'))

def _regroup_and_sum_orders(orders):
    result = []
    for restaurant, orders_of_restaurant in itertools.groupby(orders, lambda order: order.restaurant):
        summary = {'restaurant': restaurant, 'total': 0, 'total_price': 0}
        if restaurant.kind == 'C':
            summary['orders'] = {}
            for for_user, orders_of_user in itertools.groupby(orders_of_restaurant, lambda order: order.for_user):
                summary['orders'][for_user], total, total_price = _sum_orders(orders_of_user)
                summary['total'] += total
                summary['total_price'] += total_price

        else:
            summary['orders'], total, total_price = _sum_orders(orders_of_restaurant)
            summary['total'] += total
            summary['total_price'] += total_price

        result.append(summary)
        
    return result

def _sum_orders(orders):
    result = defaultdict(int)
    total = total_price = 0
    for order in orders:
        result[order.meal] += order.num
        total = order.num
        total_price = order.meal.price_today() * order.num
        
    # django template doesn't support defaultdict well
    return dict(result), total, total_price 

            
    