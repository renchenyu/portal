# -*- coding:utf8 -*-
from django import forms

class AccountDepositeForm(forms.Form):
    money = forms.DecimalField(min_value=0.01, max_digits=10, decimal_places=2, label=u"金额")
    detail = forms.CharField(widget=forms.Textarea, required=False, label=u"明细")