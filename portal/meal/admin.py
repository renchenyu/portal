from meal.models import Restaurant, PhoneNumber, Meal
from django.contrib import admin

class PhoneNumberInline(admin.StackedInline):
    model = PhoneNumber
    extra = 2
    
class MealInline(admin.StackedInline):
    model = Meal
    extra = 1

class RestaurantAdmin(admin.ModelAdmin):
    inlines = [PhoneNumberInline, MealInline]
    list_display = ['name', 'kind']

admin.site.register(Restaurant, RestaurantAdmin)
