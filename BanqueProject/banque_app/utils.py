#from mailbox import Message
from django.core.mail import EmailMessage as DjangoEmailMessage
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.contrib.auth.models import User

import json
from django.urls import reverse
from .models import Attachment, UserProfile,Message


logger = logging.getLogger(__name__)

def send_email(subject, body, from_email, to_emails, attachments=None, reply_to=None):
    """
    Envoie un email avec des options pour les pièces jointes et les adresses de réponse.

    :param subject: Sujet de l'email
    :param body: Corps de l'email
    :param from_email: Adresse email de l'expéditeur
    :param to_emails: Liste des adresses email des destinataires
    :param attachments: Liste des fichiers à joindre (optionnel)
    :param reply_to: Liste des adresses email de réponse (optionnel)
    """
    email = DjangoEmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to_emails,
        reply_to=reply_to,
    )

    if attachments:
        for attachment in attachments:
            logger.debug(f"Attaching to email: {attachment.name}")
            email.attach(attachment.name, attachment.read(), attachment.content_type)

    email.send()
    logger.info("Email sent successfully")


def send_standard_email(message, recipients, attachments):
    send_email(
        subject=message.subject,
        body=message.content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=[user.email for user in recipients],
        attachments=attachments,
        reply_to=[settings.NO_REPLY_EMAIL]
    )
    
    
def send_activation_email(user, request):
    current_site = get_current_site(request)
    mail_subject = 'Activez votre compte'
    message = render_to_string('connection/activation_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })

    send_email(
        subject=mail_subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=[user.email]
    )
    
    
def handle_attachments(message, attachments):
    """
    Gère les pièces jointes en les associant à un message.

    :param message: L'objet Message auquel les pièces jointes doivent être associées
    :param attachments: Liste des fichiers joints à traiter
    """
    for attachment in attachments:
        logger.debug(f"Processing attachment: {attachment.name}")
        # Crée un objet Attachment pour chaque fichier joint
        Attachment.objects.create(message=message, file=attachment)
        logger.debug(f"Attachment saved: {attachment.name}")
        
        




def update_status(request, model_class):
    if request.method == 'POST':
        item_id = request.POST.get('user_id')
        new_status = request.POST.get('status')
        
        if not new_status:
            return JsonResponse({'success': False, 'message': 'Le statut ne peut pas être vide'}, status=400)
        
        try:
            item = get_object_or_404(model_class, id=item_id)
            status_field = 'statut' if hasattr(item, 'statut') else 'status'
            setattr(item, status_field, new_status)
            item.save()
            return JsonResponse({
                'success': True, 
                'message': 'Statut mis à jour avec succès',
                'new_status': new_status
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return None



def handle_form_submission(request, form_class, success_message, redirect_url, extra_actions=None):
    if request.method == 'POST':
        try:
            form = form_class(request.POST)
            if form.is_valid():
                instance = form.save(commit=False)
                if hasattr(instance, 'user'):
                    instance.user = request.user
                elif hasattr(instance, 'utilisateur'):
                    instance.utilisateur = UserProfile.objects.get(user=request.user)
                
                if extra_actions:
                    extra_actions(request, form)  # Appel de extra_actions avant la sauvegarde
                
                instance.save()

                logger.info(f"{form_class.__name__} créé pour l'utilisateur {request.user.username}")
                return JsonResponse({
                    'status': 'success',
                    'message': success_message,
                    'redirect_url': reverse(redirect_url, args=[request.user.id])
                })
            else:
                logger.warning(f"Formulaire invalide pour l'utilisateur {request.user.username}: {form.errors}")
                return JsonResponse({
                    'status': 'error',
                    'errors': json.loads(json.dumps(form.errors))
                })
        except Exception as e:
            logger.error(f"Erreur lors de la création de {form_class.__name__} pour {request.user.username}: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'errors': f"Une erreur s'est produite: {str(e)}"
            })
    else:
        form = form_class()

    return form



def create_message(subject, content, user):
    message = Message.objects.create(subject=subject, content=content)
    message.recipients.set([user])
    message.save()
    
    
    
def create_user_and_profile(form_data):
    user = User.objects.create_user(
        username=form_data['username'],
        email=form_data['email'],
        password=form_data['password1']
    )
    user.is_active = False
    user.save()

    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'first_name': form_data['first_name'],
            'last_name': form_data['last_name'],
            'birth_date': form_data['birth_date'],
            'birth_place': form_data['birth_place'],
            'nationality': form_data['nationality'],
            'gender': form_data['gender'],
            'address': form_data['address'],
            'phone': form_data['phone'],
            'income': form_data['income'],
            'income_source': form_data['income_source'],
            'profession': form_data['profession'],
            'terms': form_data['terms'],
            'consent': form_data['consent'],
            'confirmation': form_data['confirmation']
        }
    )
    return user