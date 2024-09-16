from decimal import Decimal
import hashlib
import hmac
import json
import time
from django.http import HttpResponseRedirect

from django.utils import translation
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.core.mail import EmailMessage as DjangoEmailMessage
from django.contrib.auth.tokens import default_token_generator
import random
from django.conf import settings
from django.http import HttpResponseForbidden
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import stripe
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist

from bitpay.client import Client,Invoice
from bitpay.models.invoice.buyer import Buyer
from bitpay.models.facade import Facade


from banque_app.decoration import add_common_data
from banque_app.forms import CreditForm, CryptoPaymentForm, CustomAuthenticationForm, DemandePretForm, DemandeRetraitForm, IdentiteForm, MessageForm, UserProfileForm
from .utils import send_standard_email, send_activation_email, handle_attachments
from .models import Attachment, CompteBancaire, CryptoPayment, DemandePret, DemandeRetrait, Identite, PaymentHistory, UserPayment, UserProfile, Virement, Message
from django.contrib.auth.models import User
import logging
logger = logging.getLogger(__name__)

def home(request):
    user_type = ''
    user_id = ''
    if not isinstance(request.user, AnonymousUser):
        if request.user.is_authenticated:
            user_type = 'dashbord_admin' if request.user.is_superuser else 'dashbord_user'
            user_id = request.user.id
    return render(request, 'acceuille/banque.html', {"user_type": user_type, "user_id": user_id})

@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)

        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            user.is_active = False
            user.save()

            # Use get_or_create() to prevent IntegrityError if a profile already exists
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'birth_date': form.cleaned_data['birth_date'],
                    'birth_place': form.cleaned_data['birth_place'],
                    'nationality': form.cleaned_data['nationality'],
                    'gender': form.cleaned_data['gender'],
                    'address': form.cleaned_data['address'],
                    'phone': form.cleaned_data['phone'],
                    'income': form.cleaned_data['income'],
                    'income_source': form.cleaned_data['income_source'],
                    'profession': form.cleaned_data['profession'],
                    'terms': form.cleaned_data['terms'],
                    'consent': form.cleaned_data['consent'],
                    'confirmation': form.cleaned_data['confirmation']
                }
            )

            # Appeler la fonction d'envoi d'email
            send_activation_email(user, request)

            return render(request, 'connection/inscription.html', {
                'form': form,
                'alert_type': 'success',
                'alert_message': "Inscription réussie. Veuillez vérifier votre e-mail pour activer votre compte."
            })
        else:
            errors = form.errors.as_json()
            return render(request, 'connection/inscription.html', {
                'form': form,
                'alert_type': 'error',
                'alert_message': "Erreur lors de l'inscription. Veuillez vérifier les informations saisies.",
                'form_errors': errors
            })
    else:
        form = UserProfileForm()

    return render(request, 'connection/inscription.html', {'form': form})

def generate_unique_account_number():
    # Generate a 12-digit number formatted as XXXX-XXXX-XXXX
    return f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        logger.info(f"Decoded UID: {uid}")
        user = User.objects.get(pk=uid)
        logger.info(f"Found user: {user}")
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        logger.error(f"Error finding user: {e}")
        user = None

    if user is not None:
        logger.info(f"User is not None: {user}")
        if default_token_generator.check_token(user, token):
            logger.info("Token is valid")
            user.is_active = True
            user.save()

            # Create or get UserProfile
            user_profile, _ = UserProfile.objects.get_or_create(user=user)

            # Initialize CompteBancaire
            compte_bancaire, created = CompteBancaire.objects.get_or_create(
                user=user_profile,  # Use user_profile instead of user
                defaults={
                    'numero_compte': generate_unique_account_number(),
                    'solde': 0,
                }
            )
            if created:
                logger.info(f"CompteBancaire created for user {user} with account number {compte_bancaire.numero_compte}")

            # Create the message
            message = Message.objects.create(
                sender=None,  # or set to a specific admin user
                subject="Bienvenue sur notre plateforme!",
                content="Merci de nous avoir rejoints. Nous sommes heureux de vous accueillir. Votre compte est maintenant activé.",
            )

            # Add the user to the recipients
            message.recipients.add(user_profile)

            login(request, user)
            logger.info(f"User {user} activated successfully")
            return redirect('connexion')
        else:
            logger.warning(f"Invalid token for user {user}")
    else:
        logger.warning("User is None")

    logger.warning("Invalid activation link")
    return render(request, 'connection/activation_invalid.html')

def login_view(request):
    print("Vue login_view appelée")

    # Vérifier si l'utilisateur est déjà connecté
    if request.user.is_authenticated:
        print("Utilisateur déjà connecté")
        if request.user.is_superuser:
            return redirect('dashbord_admin', user_id=request.user.id)
        else:
            return redirect('dashbord_user', user_id=request.user.id)

    if request.method == 'POST':
        print("Méthode POST détectée")
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            print(f"Tentative de connexion avec {username}")
            user = authenticate(username=username, password=password)
            print(f"Apres authen   {user}")
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, 'Connexion réussie !')
                    if user.is_superuser:
                        return redirect('dashbord_admin', user_id=user.id)
                    else:
                        return redirect('dashbord_user', user_id=user.id)
                else:
                    messages.warning(request, 'Votre compte n\'est pas activé. Veuillez vérifier votre e-mail pour activer votre compte.')
            else:
                print("Échec de l'authentification")
                messages.error(request, 'Identifiants invalides.')
        else:
            print("Formulaire non valide")
            print(form.errors)  # Imprime les erreurs de formulaire pour le débogage
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')

    else:
        form = CustomAuthenticationForm()

    return render(request, 'connection/connexion.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('connexion')




@login_required(login_url='login')
@add_common_data
def dashbord_client(request, user_id):

    if request.user.is_superuser or request.user.id == user_id:
        user = get_object_or_404(User, id=user_id)

        user_profile, _ = UserProfile.objects.get_or_create(user=user)

        try:
            identite = Identite.objects.get(user=user_profile)
        except Identite.DoesNotExist:
            identite = None
            logger.warning(f"Identite not found for user {user.id}")

        virements = Virement.objects.filter(user=user).order_by('-date_creation')
        messages_user = Message.objects.filter(recipients=user.id).order_by('-timestamp')

        context = {
            'user_viewed': user,
            'profile': user_profile,
            'identite': identite,
            'virements': virements,
            'messages': messages_user,
            'template_name': 'admins/client/dashbord_client.html'
        }
        return context
    else:
        logger.warning(f"User {request.user.id} tried to access profile of user {user_id} without permission.")
        return HttpResponseForbidden("Vous n'avez pas la permission d'accéder à ce profil.")
    
    
@login_required(login_url='login')
@add_common_data
def statut_compte(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_status = request.POST.get('status')

        if not new_status:
            return JsonResponse({'success': False, 'message': 'Le statut ne peut pas être vide'}, status=400)

        try:
            user_profile = UserProfile.objects.get(id=user_id)
            user_profile.statut = new_status
            user_profile.save()
            return JsonResponse({
                'success': True,
                'message': 'Statut mis à jour avec succès',
                'new_status': new_status
            })
        except UserProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Profil utilisateur non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    user_profiles = UserProfile.objects.all()
    context = {
        'user_profiles': user_profiles,
        'template_name': 'admins/administation/status_compte.html'
    }
    return context

@login_required(login_url='login')
@add_common_data
def statut_demande_pret(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_status = request.POST.get('status')

        if not new_status:
            return JsonResponse({'success': False, 'message': 'Le statut ne peut pas être vide'}, status=400)

        try:
            user_profile = DemandePret.objects.get(id=user_id)
            user_profile.statut = new_status
            user_profile.save()
            return JsonResponse({
                'success': True,
                'message': 'Statut mis à jour avec succès',
                'new_status': new_status
            })
        except UserProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Profil utilisateur non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    demandes_prets = DemandePret.objects.all()
    context = {
        'demandes_prets': demandes_prets,
        'template_name': 'admins/administation/status_demande_pret.html'
    }
    return context

@login_required(login_url='login')
@add_common_data
def statut_demande_retrait(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_status = request.POST.get('status')

        if not new_status:
            return JsonResponse({'success': False, 'message': 'Le statut ne peut pas être vide'}, status=400)

        try:
            user_profile = DemandeRetrait.objects.get(id=user_id)
            user_profile.status = new_status
            user_profile.save()
            return JsonResponse({
                'success': True,
                'message': 'Statut mis à jour avec succès',
                'new_status': new_status
            })
        except UserProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Profil utilisateur non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    demandes_retraits = DemandeRetrait.objects.all()
    context = {
        'demandes_retraits': demandes_retraits,
        'template_name': 'admins/administation/status_demande_retraits.html'
    }
    return context

@login_required(login_url='login')
@transaction.atomic
def create_checkout_session(request, pret_id):
    if request.method == 'POST':
        try:
            user_id = request.user.id
            logger.info(f"Création de session de paiement pour l'utilisateur {user_id}")

            user_demand_pret = DemandePret.objects.get(id=pret_id)

            if not user_demand_pret:
                logger.error(f"Aucune demande de prêt trouvée pour l'utilisateur {user_id}")
                return JsonResponse({'error': 'Aucune demande de prêt trouvée pour cet utilisateur'}, status=404)

            if user_demand_pret.statut != "APPROUVE":
                logger.error(f"Cette demande de pret n'est pas encore accordé  {user_demand_pret}")
                return JsonResponse({'error': "Cette demande de pret n'est pas encore accordé"}, status=404)

            try:
                amount_requested = float(user_demand_pret.montant_demande)
                taux = float(user_demand_pret.taux_interet)
                amount_to_pay = int(amount_requested * taux * 100)
                logger.info(f"Montant à payer calculé : {amount_to_pay} centimes")
            except ValueError as e:
                logger.error(f"Erreur dans le calcul du montant : {str(e)}")
                return JsonResponse({'error': 'Erreur dans le calcul du montant'}, status=400)

            try:
                stripe.api_key = settings.STRIPE_SECRET_KEY_TEST
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[
                        {
                            'price_data': {
                                'currency': 'eur',
                                'unit_amount': amount_to_pay,
                                'product_data': {
                                    'name': 'Remboursement de prêt',
                                },
                            },
                            'quantity': 1,
                        },
                    ],
                    mode='payment',
                    customer_creation='always',
                    success_url=request.build_absolute_uri(reverse('payment-result')) + '?status=success&session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=request.build_absolute_uri(reverse('payment-result')) + '?status=cancel',
                )
                logger.info(f"Session Stripe créée avec succès : {checkout_session.id}")

                user_demand_pret.paiement_effectue = True
                user_demand_pret.save()

                # Créer un enregistrement PaymentHistory en attente

                try:
                    user_payment, created = UserPayment.objects.get_or_create(
                        app_user=request.user.userprofile,
                        defaults={'demande_pret': user_demand_pret}
                    )
                    if created:
                        logger.info(f"UserPayment created for user {request.user.userprofile} with loan {user_demand_pret.id}")
                except DemandePret.DoesNotExist:
                    logger.error(f"DemandePret not found for id {pret_id}")
                    return JsonResponse({'error': 'Demande de prêt introuvable'}, status=404)

                message = Message.objects.create(
                    subject="Confirmation de votre paiement",
                    content=f"<h3>Cher(e) {request.user.username},</h3><br><p>Nous vous remercions d'avoir effectué votre paiement de {amount_to_pay} avec succès. Votre paiement est en cours de traitement et fera l'objet d'un examen approfondi par nos services. Veuillez noter que votre compte sera crédité du montant {amount_requested} dès que cet examen sera terminé. Nous vous tiendrons informé(e) dès que cette opération sera finalisée. Nous vous remercions pour votre confiance et restons à votre disposition pour toute question supplémentaire.</p>"
                )
                message.recipients.set([request.user.id])
                message.save()

                PaymentHistory.objects.create(
                    user_payment=user_payment,
                    amount=amount_to_pay / 100,  # Convertir en euros
                    status='PENDING',
                    stripe_checkout_session_id=checkout_session.id
                ).save()

                return JsonResponse({'sessionId': checkout_session.id})
            except stripe.error.StripeError as e:
                logger.error(f"Erreur Stripe : {str(e)}")
                return JsonResponse({'error': 'Erreur Stripe : ' + str(e)}, status=500)

        except Exception as e:
            logger.exception("Erreur inattendue lors de la création de la session de paiement")
            return JsonResponse({'error': 'Erreur serveur : ' + str(e)}, status=500)

    return JsonResponse({'error': 'Requête invalide'}, status=400)

@transaction.atomic
@add_common_data
def payment_result(request):
    status = request.GET.get('status')
    session_id = request.GET.get('session_id')

    logger.info(f"Payment result called with status: {status}, session_id: {session_id}")

    context = {
        'status': status,
        'session_id': session_id,
        'template_name': 'admins/client/resultats.html'
    }

    if status == 'success':
        stripe.api_key = settings.STRIPE_SECRET_KEY_TEST
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            customer = stripe.Customer.retrieve(session.customer)
            user_profile = request.user.userprofile
            logger.info(f"Retrieved Stripe session and customer for user: {request.user.username}")

            user_payment = UserPayment.objects.get(app_user=user_profile)

            user_payment.stripe_customer_id = customer.id
            user_payment.payment_bool = True

            user_payment.save()

            # Mettre à jour PaymentHistory
            payment_history = PaymentHistory.objects.filter(
                user_payment=user_payment,
                stripe_payment_intent_id=session.payment_intent
            ).first()

            if payment_history:
                payment_history.status = 'SUCCESS'
                payment_history.save()
                logger.info(f"Updated PaymentHistory for user: {request.user.username}, session_id: {session_id}")
            else:
                logger.warning(f"PaymentHistory not found for session_id: {session_id}")

            context['customer'] = customer
        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile not found for user: {request.user.username}")
            context['error'] = "Erreur: Profil utilisateur non trouvé."
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error occurred: {str(e)}")
            context['error'] = f"Erreur Stripe: {str(e)}"
        except Exception as e:
            logger.exception(f"Unexpected error occurred: {str(e)}")
            context['error'] = f"Une erreur inattendue s'est produite: {str(e)}"
    elif status == 'cancel':
        # Mettre à jour PaymentHistory pour les paiements annulés
        try:
            payment_history = PaymentHistory.objects.filter(
                user_payment__app_user=request.user.userprofile,
                status='PENDING'
            ).latest('timestamp')
            payment_history.status = 'FAILURE'
            payment_history.failure_reason = "Paiement annulé par l'utilisateur"
            payment_history.save()
            logger.info(f"Updated PaymentHistory for cancelled payment: {request.user.username}")
        except PaymentHistory.DoesNotExist:
            logger.warning(f"No pending PaymentHistory found for cancelled payment: {request.user.username}")

    logger.info(f"Returning context: {context}")
    return context

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY_TEST
    logger.info("Stripe webhook called")

    payload = request.body
    signature_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, signature_header, settings.STRIPE_WEBHOOK_SECRET_TEST
        )
        logger.info(f"Stripe event constructed: {event['type']}")
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session.get('id', None)
        payment_intent_id = session.get('payment_intent', None)
        logger.info(f"Checkout session completed: {session_id}")

        try:
            payment_history = PaymentHistory.objects.get(stripe_payment_intent_id=payment_intent_id)
            payment_history.status = 'SUCCESS'
            payment_history.save()

            user_payment = payment_history.user_payment
            user_payment.payment_bool = True
            user_payment.save()

            logger.info(f"PaymentHistory and UserPayment updated for session_id: {session_id}")
        except PaymentHistory.DoesNotExist:
            logger.error(f"PaymentHistory not found for payment_intent_id: {payment_intent_id}")
        except Exception as e:
            logger.exception(f"Error updating PaymentHistory: {str(e)}")

    return HttpResponse(status=200)

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def dashboard_admin(request, user_id):
    user_profiles = UserProfile.objects.select_related('user').all()
    context = {
        "user_profiles": user_profiles,
        'user_id': user_id
    }
    return render(request, 'admins/administation/comptes.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def compte_banque(request):
    comptes = CompteBancaire.objects.all()
    return render(request, 'admins/administation/comptes_banquaires.html', {'comptes': comptes})

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def crediter_compte(request, compte_id):
    compte = get_object_or_404(CompteBancaire, id=compte_id)

    form = CreditForm(request.POST)
    if form.is_valid():
        montant = form.cleaned_data['montant']
        try:
            print("---------------------")
            with transaction.atomic():
                # Met à jour le solde du compte
                compte.solde += montant
                compte.save()

                message = Message.objects.create(
                    sender=request.user,
                    subject="Votre compte a été crédité",
                    content=f"Votre compte {compte.numero_compte} a été crédité de {montant}€.",
                    no_reply=True
                )
                # Ajout du destinataire
                message.recipients.add(compte.user)
            # Retourne une réponse JSON de succès
            return JsonResponse({
                'success': True,
                'message': f"Le compte {compte.numero_compte} a été crédité de {montant}€."
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Une erreur s'est produite lors du crédit : {str(e)}"
            })
    else:
        return JsonResponse({
            'success': False,
            'message': "Formulaire invalide"
        })

@login_required
@add_common_data
def demande_retrait(request):
    if request.method == 'POST':
        try:
            form = DemandeRetraitForm(request.POST, user=request.user)
            if form.is_valid():
                withdrawal_request = form.save(commit=False)
                withdrawal_request.user = request.user
                withdrawal_request.save()
                message = Message.objects.create(
                    subject=f"Votre demande de retrait est de {form.cleaned_data['amount']} € en attente de traitement",
                    content="Votre demande de retrait a bien été prise en compte et est actuellement en attente de traitement. Nous mettons tout en œuvre pour que celle-ci soit traitée dans les meilleurs délais. Vous serez informé par notification dès que votre retrait aura été traité avec succès. Merci pour votre patience et votre confiance."
                )
                message.recipients.set([request.user])
                message.save()
                logger.info(f"Demande de retrait créée pour l'utilisateur {request.user.username}")
                return JsonResponse({
                    'status': 'success',
                    'message': "Votre demande de retrait a été soumise avec succès.",
                    'redirect_url': reverse('dashbord_user', args=[request.user.id])
                })
            else:
                logger.warning(f"Formulaire invalide pour l'utilisateur {request.user.username}: {form.errors}")
                return JsonResponse({
                    'status': 'error',
                    'errors': json.loads(json.dumps(form.errors))
                })
        except Exception as e:
            logger.error(f"Erreur lors de la création de la demande de retrait pour {request.user.username}: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'errors': f"Une erreur s'est produite: {str(e)}"
            })
    else:
        form = DemandeRetraitForm(user=request.user)

    retraits = DemandeRetrait.objects.filter(user=request.user).order_by('-id')
    context = {
        'retraits': retraits,
        'form': form,
        'template_name': 'admins/client/demande_retrait.html'
    }
    return context

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Création et sauvegarde du message
                message = form.save(commit=False)
                message.sender = request.user
                message.no_reply = True
                message.save()

                # Ajout des destinataires
                recipients = form.cleaned_data['recipients']
                message.recipients.set(recipients)

                # Gestion des pièces jointes
                attachments = form.cleaned_data.get('attachments', [])
                logger.debug(f"Attachments: {attachments}")

                if attachments:
                    handle_attachments(message, attachments)

                # Préparation et envoi de l'email
                send_standard_email(
                    message=message,
                    recipients=recipients,
                    attachments=attachments
                )

                messages.success(request, "Le message a été envoyé avec succès.")
                return redirect('compte_banque')

            except Exception as e:
                logger.error(f"Error sending message: {str(e)}", exc_info=True)
                messages.error(request, f"Une erreur s'est produite lors de l'envoi du message : {str(e)}")
                # Si une erreur se produit, on supprime le message partiellement créé
                if message.id:
                    message.delete()
        else:
            logger.warning(f"Form errors: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = MessageForm()

    return render(request, 'admins/administation/send_mail.html', {'form': form})

@add_common_data
def info_user(request, user_id):
    context = {
        'template_name': 'admins/client/information_perso.html'
    }
    return context

@add_common_data
def demande_pret_view(request):

    if request.method == 'POST':
        form = DemandePretForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            user_profil = UserProfile.objects.get(user=request.user)
            demande.utilisateur = user_profil  # Associer l'utilisateur connecté à la demande
            demande.statut = 'EN_ATTENTE'
            demande.taux_interet = 0.1
            demande.save()
            montant = form.cleaned_data['montant_demande']
            message = Message.objects.create(
                subject="Votre demande de prêt est en attente de traitement",
                content=f"<h3>Cher(e) {request.user.username},</h3><br><p>Nous avons bien reçu votre demande de prêt d'un montant de {montant}. <br> Votre demande est actuellement en attente de traitement et sera examinée par notre équipe dans les plus brefs délais. Nous vous tiendrons informé(e) de l'avancement de votre dossier et vous contacterons dès que celui-ci sera traité.<br> Nous vous remercions de votre confiance et restons à votre disposition pour toute information complémentaire.</p>"
            )
            message.recipients.set([request.user.id])
            message.save()
            return redirect('list_demande')  # Remplacez par l'URL de succès appropriée
    else:
        form = DemandePretForm()

    context = {
        'template_name': 'admins/client/demande_pret.html',
        'form': form
    }
    return context

@add_common_data
def list_demande(request):

    context = {
        'listes': DemandePret.objects.all().order_by("-id"),
        'template_name': 'admins/client/list_demende_pret.html',
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY_TEST,
    }
    return context

@add_common_data
def message(request):
    context = {
        'messages': Message.objects.all().order_by("-id"),
        'template_name': 'admins/client/message.html',
    }
    return context

@transaction.atomic
@login_required
@add_common_data
def update_identite(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        identite = Identite.objects.get(user=user_profile)
    except Identite.DoesNotExist:
        identite = Identite(user=user_profile)

    if request.method == 'POST':
        form = IdentiteForm(request.POST, request.FILES, instance=identite)
        if form.is_valid():
            identite = form.save(commit=False)
            identite.user = user_profile
            identite.save()

            user_profile.statut = 'En attente de vérification'
            user_profile.save()

            return redirect('dashbord_user', user_id=request.user.id)
    else:

        form = IdentiteForm(instance=identite)
    context = {
        'form': form,
        'template_name': 'admins/client/verification.html',
    }
    return context

@login_required
@add_common_data
def historiques(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    historiques = PaymentHistory.objects.filter(user_payment__app_user=user_profile).order_by('-id')

    context = {
        'historiques': historiques,
        'template_name': 'admins/client/historique_client.html',
    }

    return context





# bitpay_client = Client(api_token=settings.BITPAY_API_TOKEN, environment=settings.BITPAY_ENVIRONMENT)

# @login_required
# @add_common_data
# def create_crypto_payment(request):
#     if request.method == 'POST':
#         form = CryptoPaymentForm(request.POST)
#         if form.is_valid():
#             amount = form.cleaned_data['amount']
#             crypto_currency = form.cleaned_data['crypto_currency']
            
#             try:
#                 invoice = bitpay_client.create_invoice({
#                     "price": float(amount),
#                     "currency": crypto_currency,
#                     "notificationURL": request.build_absolute_uri('/bitpay-webhook/'),
#                     "redirectURL": request.build_absolute_uri('/check-payment-status/'),
#                 })
                
#                 payment = CryptoPayment.objects.create(
#                     user=request.user,
#                     amount=amount,
#                     crypto_currency=crypto_currency,
#                     bitpay_invoice_id=invoice['id']
#                 )
                
#                 return JsonResponse({
#                     'success': True,
#                     'redirect_url': invoice['url']
#                 })
#             except Exception as e:
#                 print(f"Error creating BitPay invoice: {str(e)}")
#                 return JsonResponse({
#                     'success': False,
#                     'error': "An error occurred while processing your payment. Please try again."
#                 })
#     else:
#         form = CryptoPaymentForm()
        
#     context = {
#         'form': form,
#         'template_name': 'admins/client/create_crypto_payment.html'
#     }
#     return context
# @login_required
# def check_payment_status(request):
#     payment_id = request.GET.get('payment_id')
#     try:
#         payment = CryptoPayment.objects.get(bitpay_invoice_id=payment_id, user=request.user)
#         return JsonResponse({
#             'success': True,
#             'status': payment.status
#         })
#     except CryptoPayment.DoesNotExist:
#         return JsonResponse({
#             'success': False,
#             'error': "Payment not found"
#         })

# def verify_bitpay_signature(payload, signature):
#     secret = settings.BITPAY_WEBHOOK_SECRET
#     computed_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
#     return hmac.compare_digest(computed_signature, signature)

# @csrf_exempt
# @require_POST
# def bitpay_webhook(request):
#     try:
#         payload = request.body
#         signature = request.headers.get('X-Signature')

#         if not verify_bitpay_signature(payload, signature):
#             return HttpResponse("Invalid signature", status=401)

#         data = json.loads(payload)
#         event = data['event']
#         invoice = data['data']

#         payment = CryptoPayment.objects.get(bitpay_invoice_id=invoice['id'])
#         payment.status = invoice['status']
#         payment.save()

#         # Logique supplémentaire basée sur le statut
#         if payment.status == 'confirmed':
#             # Traiter le paiement confirmé
#             pass
#         elif payment.status == 'complete':
#             # Traiter le paiement complet
#             pass
#         elif payment.status == 'invalid':
#             # Gérer les paiements invalides
#             pass

#         return HttpResponse("OK", status=200)
#     except json.JSONDecodeError:
#         return HttpResponse("Invalid JSON", status=400)
#     except CryptoPayment.DoesNotExist:
#         return HttpResponse("Payment not found", status=404)
#     except Exception as e:
#         print(f"Error processing webhook: {str(e)}")
#         return HttpResponse("Error processing webhook", status=500)