# -*- coding:utf8 -*-
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User


class Restaurant(models.Model):
    name = models.CharField(max_length=50, verbose_name=u'名称')
    
    KIND_CHOCIES = (
        ('S', u'单点(如：普通盒饭)'),
        ('M', u'多点(如：粥店)'),
        ('C', u'XX(如：麻辣烫)')
    )
    kind = models.CharField(max_length=1, choices=KIND_CHOCIES, verbose_name=u'类型', default='S')
    
    def __unicode__(self):
        return unicode(self.name)
    
class PhoneNumber(models.Model):
    restaurant = models.ForeignKey(Restaurant)
    number = models.CharField(max_length=20, verbose_name=u'电话号码')
    
    def __unicode__(self):
        return unicode(self.number)
    
class Meal(models.Model):
    restaurant = models.ForeignKey(Restaurant)
    name = models.CharField(max_length=50, verbose_name=u'名字')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=u'价格')
    
    WEEKDAY_CHOICES = (
        ('0', u'无'),
        ('1', u'星期一'),
        ('2', u'星期二'),
        ('3', u'星期三'),
        ('4', u'星期四'),
        ('5', u'星期五'),
        ('6', u'星期六'),
        ('7', u'星期日'),                   
        
    )
    special_offer_weekday = models.CharField(max_length=1, verbose_name=u'特价日', choices=WEEKDAY_CHOICES, default='0')
    speical_offer_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=u'特价')
    
    def __unicode__(self):
        return unicode(self.name)
    
    def price_today(self):
        if int(self.special_offer_weekday) == datetime.today().weekday() + 1:
            return self.speical_offer_price
        else:
            return self.price
        
    
class Order(models.Model):
    order_user = models.ForeignKey(User, related_name="order_by_myself")
    for_user = models.ForeignKey(User, related_name="order_for_me")
    meal = models.ForeignKey(Meal)
    restaurant = models.ForeignKey(Restaurant)
    num = models.PositiveSmallIntegerField()
    state = models.PositiveSmallIntegerField(default=0)
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)
    
    @classmethod
    def today(cls):
        today = datetime.today()
        return cls.by_date(today.year, today.month, today.day)
        
    @classmethod
    def by_date(cls, year, month, day):
        return Order.objects.filter(created_datetime__year=year,
            created_datetime__month=month, created_datetime__day=day)
    
class Lock(models.Model):
    locked = models.BooleanField(default=False)
    
    @classmethod
    def is_locked(cls):
        lock = cls.objects.get_or_create(pk=1)[0]
        return lock.locked
    
    @classmethod
    def toggle(cls):
        lock = cls.objects.get_or_create(pk=1)[0]
        lock.locked = not lock.locked
        lock.save()
        
    @classmethod
    def unlock(cls):
        lock = cls.objects.get_or_create(pk=1)[0]
        lock.locked = False
        lock.save()
        
    @classmethod
    def lock(cls):
        lock = cls.objects.get_or_create(pk=1)[0]
        lock.locked = True
        lock.save()
        
        
        
        

    
    
    
