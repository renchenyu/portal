from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db.models import F

class Account(models.Model):
    user = models.OneToOneField(User)
    
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def deposite(self, money, operator, detail=""):
        if money > 0:
            self.balance = F('balance') + money
            self.save()
            self.log_set.create(
                operator=operator,
                income=money,
                detail=detail 
            )
        else:
            raise ValueError()
        
    def withdraw(self, money, detail):
        if money > 0:
            self.balance = F('balance') - money
            self.save()
            self.log_set.create(
                operator=self.user,
                income=-money,
                detail=detail
            )
        else:
            raise ValueError()
    
    class Meta:
        permissions = (
            ("deposite_account", "Can deposit account"),
        )

def create_account(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(user=instance)

#create an account for a new created user
post_save.connect(create_account, sender=User)
    
class Log(models.Model):
    account = models.ForeignKey(Account)
    operator = models.ForeignKey(User)
    
    income = models.DecimalField(max_digits=10, decimal_places=2)
    datetime = models.DateTimeField(auto_now_add=True)
    detail = models.TextField()
    

    
