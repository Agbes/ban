from django.contrib import admin
from .models import UserProfile, Identite, DemandePret, CrediteCompte, Virement, CompteBancaire, DemandeRetrait, Message, Attachment, UserPayment, PaymentHistory

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'profession', 'statut')
    search_fields = ('user__username', 'phone', 'address')
    list_filter = ('gender', 'profession', 'statut')

@admin.register(Identite)
class IdentiteAdmin(admin.ModelAdmin):
    list_display = ('user', 'iban', 'cnss', 'number_carte_passport')
    search_fields = ('user__username', 'iban', 'cnss', 'number_carte_passport')

@admin.register(DemandePret)
class DemandePretAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'montant_demande', 'duree', 'taux_interet', 'statut', 'date_demande')
    search_fields = ('utilisateur__user__username', 'montant_demande', 'motif')
    list_filter = ('statut',)

@admin.register(CrediteCompte)
class CrediteCompteAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'numero_compte', 'montant', 'devise', 'reference_transaction', 'date_transaction')
    search_fields = ('utilisateur__username', 'numero_compte', 'reference_transaction')
    list_filter = ('devise',)

@admin.register(Virement)
class VirementAdmin(admin.ModelAdmin):
    list_display = ('user', 'montant', 'statut', 'date_creation')
    search_fields = ('user__username', 'montant')
    list_filter = ('statut',)

@admin.register(CompteBancaire)
class CompteBancaireAdmin(admin.ModelAdmin):
    list_display = ('user', 'numero_compte', 'solde')
    search_fields = ('user__username', 'numero_compte')

@admin.register(DemandeRetrait)
class DemandeRetraitAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'status', 'created_at', 'updated_at')
    search_fields = ('user__username', 'amount')
    list_filter = ('status',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'subject', 'timestamp', 'is_read', 'no_reply')
    search_fields = ('sender__username', 'subject')
    list_filter = ('is_read', 'no_reply')

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('message', 'file')
    search_fields = ('message__subject',)

@admin.register(UserPayment)
class UserPaymentAdmin(admin.ModelAdmin):
    list_display = ('app_user', 'payment_bool', 'stripe_customer_id', 'demande_pret')
    search_fields = ('app_user__user__username', 'stripe_customer_id')

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('user_payment', 'amount', 'status', 'timestamp', 'stripe_payment_intent_id', 'failure_reason')
    search_fields = ('user_payment__app_user__user__username', 'stripe_payment_intent_id', 'status')
    list_filter = ('status',)
