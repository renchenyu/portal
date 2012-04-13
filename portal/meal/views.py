# -*- coding:utf8 -*-
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseNotFound, HttpResponseRedirect, HttpResponseNotAllowed, \
    HttpResponseForbidden
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import transaction

from meal.models import Order, Restaurant, Meal, Lock

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
def order(request):
    if request.method == 'POST':
        
        # disable this function if meal system has been locked
        if Lock.is_locked():
            return HttpResponseForbidden('订餐系统已经锁定')
        
        meal_ids = request.POST.getlist('meal_ids')
        meals = Meal.objects.in_bulk(meal_ids)
        
        if len(meals) == 0:
            return HttpResponseRedirect(reverse('meal.views.menu'))
            
        try:
            payer_id = request.POST['payer_id']
            payer = request.user
            if payer_id != payer.id:
                payer = User.objects.get(pk=payer_id)
                
            orders = []
            for id, meal in meals.iteritems():
                num = request.POST['num_' + str(id)]
                try:
                    num = int(num)
                except ValueError:
                    num = 1
                print meal
                print meal.restaurant
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
    
    orders = orders.select_related('meal', 'restaurant', 'order_for').order_by('restaurant')
  
    # data for unorderd users      
    ordered_user_set = set([order.for_user for order in orders])
    all_user_set = set([user for user in User.objects.all()])
    
    # is meal sys locked?
    locked = Lock.is_locked()
        
    return render_to_response('meal/list.html', {'orders': orders,
        'orders_group_by_restaurant': _regroup_and_sum_orders(orders),
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
def cancel_order(request, order_id):
    
    # disable this function if meal system has been locked
    # TODO: can I implement this with decorator?
    if Lock.is_locked():
        return HttpResponseForbidden('订餐系统已经锁定')
    
    try:
        order = Order.objects.get(pk=order_id)
        if order.order_user == request.user or order.for_user == request.user:
            order.delete()
    except Order.DoseNotExist:
        pass
        
    return HttpResponseRedirect(reverse('meal.views.summary'))
    

def _regroup_and_sum_orders(orders):
    #TODO: refactory these ugly codes
    orders_group_by_restaurant = []
    last_restaurant_id = None
    for order in orders:
        if last_restaurant_id is None or order.restaurant.id != last_restaurant_id:
            # meet a new restaurant
            last_restaurant_id = order.restaurant.id

            current_group = {'restaurant': order.restaurant, 'total': order.num, 'total_price': order.num * order.meal.price_today()}
            if order.restaurant.kind == 'C':
                current_group['orders'] = {
                    order.for_user: {
                        order.meal: order.num,                 
                    }
                }
            else:
                current_group['orders'] = {
                    order.meal: order.num,               
                }

            orders_group_by_restaurant.append(current_group)
        else:
            current_group = orders_group_by_restaurant[-1]
            current_group_orders = current_group['orders']
            if order.restaurant.kind == "C":
                if order.for_user in current_group_orders:
                    if order.meal in current_group_orders[order.for_user]:
                        current_group_orders[order.for_user][order.meal] += order.num
                    else:
                        current_group_orders[order.for_user][order.meal] = order.num
                else:
                    current_group_orders[order.for_user] = {
                        order.meal: order.num                          
                    }
            else:
                if order.meal in orders:
                    current_group_orders[order.meal] += order.num
                else:
                    current_group_orders[order.meal] = order.num
                    
            current_group['total'] += order.num
            current_group['total_price'] += order.num * order.meal.price_today()
            
    return orders_group_by_restaurant
        
            
    