import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from functools import wraps
from .models import Identite, UserProfile, Virement, Message

logger = logging.getLogger(__name__)

def add_common_data(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        users = request.user
        try:
            user_profile = UserProfile.objects.get(user=users)
        except UserProfile.DoesNotExist:
            user_profile = None

        try:
            identite = Identite.objects.get(user=user_profile)
        except Identite.DoesNotExist:
            identite = None

        virements = Virement.objects.filter(user=users).order_by('-date_creation')
        messages_user = Message.objects.filter(recipients=user_profile).order_by('-timestamp')

        common_context = {
            'profile': user_profile,
            'is_admin': users.is_superuser,
            'virements': virements,
            'messages': messages_user,
            'identite': identite
        }

        response = view_func(request, *args, **kwargs)

        if isinstance(response, dict):
            response.update(common_context)
            return render(request, response.pop('template_name'), response)
        elif hasattr(response, 'context_data'):
            response.context_data.update(common_context)
            return response
        else:
            return response

    return wrapper

