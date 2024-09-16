from django.urls import path
from .views import *
urlpatterns = [
    path('',home,name='home'),


   path('register/',register,name="register"),
   path('activate/<uidb64>/<token>/', activate, name='activate'),
   path('connexion/',login_view,name="connexion"),
   path('logout/', logout_view, name='logout'),



   path('admininistratif/<int:user_id>/', dashboard_admin, name='dashbord_admin'),
   path('client/<int:user_id>/', dashbord_client, name='dashbord_user'),
   path('demande-retrait/', demande_retrait, name='demande_retrait'),  
   path('update_identite/', update_identite, name='update-identite'),
   
   path('demande-pret/', demande_pret_view, name='demande_pret'),
   path('list-demande-pret/', list_demande, name='list_demande'),
   path('crediter-compte/<int:compte_id>/', crediter_compte, name='crediter_compte'),
   path('comptes-bancaires/', compte_banque, name='compte_banque'),
   path('admininistratif/statut_demande_retraits/', statut_demande_retrait, name='statut_demande_retrait'),
   
   path('send-message/', send_message, name='send_message'),  
   path('info/<int:user_id>/', info_user, name='info_user'),
   path('historiques/', historiques, name='historiques'), 
   path('messages/', message, name='messages'),
   path('admininistratif/statut_compte/', statut_compte, name='statut_compte'),
   path('admininistratif/statut_demande_pret/', statut_demande_pret, name='statut_demande_pret'),
   
   path('create-checkout-session/<int:pret_id>/', create_checkout_session, name='create-checkout-session'),
   path('payment_result/', payment_result, name='payment-result'),
   path('stripe_webhooks', stripe_webhook, name='stripe-webhook'),


    # path('create-crypto-payment/', create_crypto_payment, name='create_crypto_payment'),
    # path('check-payment-status/', check_payment_status, name='check_payment_status'),
    # path('bitpay-webhook/', bitpay_webhook, name='bitpay_webhook'),

]