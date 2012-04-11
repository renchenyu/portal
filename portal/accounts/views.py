from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response

@login_required
def profile(request, template_name):
    user = request.user
    return render_to_response(template_name, {'user': user})

    
