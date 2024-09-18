from modeltranslation.translator import register, TranslationOptions
from .models import UserProfile, Identite, DemandePret, CrediteCompte, Virement, CompteBancaire, DemandeRetrait, Message

@register(UserProfile)
class UserProfileTranslationOptions(TranslationOptions):
    fields = ('birth_place', 'nationality', 'address', 'income_source', 'profession')

@register(Identite)
class IdentiteTranslationOptions(TranslationOptions):
    fields = ('iban', 'cnss')

@register(DemandePret)
class DemandePretTranslationOptions(TranslationOptions):
    fields = ('motif', 'commentaires_banque')

@register(CrediteCompte)
class CrediteCompteTranslationOptions(TranslationOptions):
    fields = ('description', 'emetteur')

@register(Virement)
class VirementTranslationOptions(TranslationOptions):
    fields = ('message_admin',)

@register(Message)
class MessageTranslationOptions(TranslationOptions):
    fields = ('subject', 'content')