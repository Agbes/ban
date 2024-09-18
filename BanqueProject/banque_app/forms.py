from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.forms.widgets import ClearableFileInput
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import CompteBancaire, DemandePret, DemandeRetrait, Identite, UserProfile, Message

from django.db import transaction

class UserProfileForm(UserCreationForm):
    username = forms.CharField(
        label=_("Nom d'utilisateur"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    first_name = forms.CharField(
        label=_("Prénoms"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    last_name = forms.CharField(
        label=_("Nom de famille"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    birth_date = forms.DateField(
        label=_("Date de naissance"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True
    )
    birth_place = forms.CharField(
        label=_("Lieu de naissance"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    nationality = forms.CharField(
        label=_("Nationalité"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    gender = forms.ChoiceField(
        label=_("Genre"),
        choices=UserProfile.GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        label=_("Adresse postale complète"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    phone = forms.CharField(
        label=_("Numéro de téléphone"),
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    email = forms.EmailField(
        label=_("Adresse email"),
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )
    income = forms.DecimalField(
        label=_("Revenu mensuel ou annuel"),
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        required=True
    )
    income_source = forms.CharField(
        label=_("Source de revenus"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )

    profession =forms.ChoiceField(
        label=_("Situation professionnelle"),
        choices=UserProfile.PROFESSION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    password2 = forms.CharField(
        label=_("Confirmer le mot de passe"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    security_question = forms.CharField(
        label=_("Question de sécurité"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    security_answer = forms.CharField(
        label=_("Réponse à la question de sécurité"),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    pin = forms.CharField(
        label=_("Code PIN (4 chiffres)"),
        max_length=4,
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'number'}),
        required=True
    )
    terms = forms.BooleanField(
        label=_("J'accepte les conditions générales"),
        required=True
    )
    consent = forms.BooleanField(
        label=_("Je consens au traitement de mes données personnelles"),
        required=True
    )
    confirmation = forms.BooleanField(
        label=_("Je confirme l'exactitude des informations fournies"),
        required=True
    )

    class Meta:
        model = User
        fields = ('username','last_name','first_name', 'email', 'password1', 'password2')

    @transaction.atomic  # Use transactions to ensure data consistency
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            # Create UserProfile immediately after saving the user
            UserProfile.objects.create(
                user=user,
                birth_date=self.cleaned_data['birth_date'],
                birth_place=self.cleaned_data['birth_place'],
                nationality=self.cleaned_data['nationality'],
                gender=self.cleaned_data['gender'],
                address=self.cleaned_data['address'],
                phone=self.cleaned_data['phone'],
                income=self.cleaned_data['income'],
                income_source=self.cleaned_data['income_source'],
                profession=self.cleaned_data['profession'],
                terms=self.cleaned_data['terms'],
                consent=self.cleaned_data['consent'],
                confirmation=self.cleaned_data['confirmation']
            )
        return user

    

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Adresse e-mail',
        max_length=254,
        widget=forms.TextInput(attrs={'id': 'login-username', 'required': 'required'})
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'id': 'login-password', 'required': 'required'})
    )


class CreditForm(forms.Form):
    montant = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)


class DemandeRetraitForm(forms.ModelForm):
    class Meta:
        model = DemandeRetrait
        fields = ['amount']
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs.update({'class': 'form-control'})

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        user = self.user
        
        if not user:
            raise forms.ValidationError("Utilisateur non spécifié.")
        
        # Récupérer le compte bancaire de l'utilisateur
        try:
            compte_bancaire = CompteBancaire.objects.get(user=user)
        except CompteBancaire.DoesNotExist:
            raise forms.ValidationError("Aucun compte bancaire n'est associé à cet utilisateur.")
        
        # Vérifier si le montant demandé dépasse le solde disponible
        if amount > compte_bancaire.solde:
            raise forms.ValidationError("Le montant demandé dépasse votre solde disponible.")
        
        if amount == compte_bancaire.solde:
            raise forms.ValidationError("Le montant demandé doit etre superieur à 0 €")
        
        return amount

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class MessageForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label='Destinataires'
    )
    subject = forms.CharField(
        max_length=255,
        label='Sujet',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    content = forms.CharField(
        label='Contenu du message',
        widget=forms.Textarea(attrs={'class': 'form-control'})
    )
    attachments = MultipleFileField(
        required=False,
        label='Pièces jointes',
        widget=MultipleFileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Message
        fields = ['recipients', 'subject', 'content']

    def clean_attachments(self):
        attachments = self.cleaned_data.get('attachments')
        for file in attachments:
            if file.size > 5 * 1024 * 1024:  # Limit file size to 5MB
                raise forms.ValidationError(f"{file.name} est trop volumineux (max 5MB).")
        return attachments

    
    
class DemandePretForm(forms.ModelForm):
    utilisateur = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.HiddenInput(),
        required=False
    )
    montant_demande = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label='Montant demandé en Euro',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    duree = forms.IntegerField(
        label='Durée en mois',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    motif = forms.CharField(
        label='Motif de la demande',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    taux_interet = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.HiddenInput(),
        required=False
    )
    statut = forms.CharField(
        max_length=20,
        widget=forms.HiddenInput(),
        required=False
    )
    commentaires_banque = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = DemandePret
        fields = ['utilisateur', 'montant_demande', 'duree', 'motif', 'taux_interet', 'statut', 'commentaires_banque']

        
        
class IdentiteForm(forms.ModelForm):
    class Meta:
        model = Identite
        fields = ['iban', 'id_photo', 'cnss', 'number_carte_passport']
        labels = {
            'iban': 'Numéro IBAN',
            'id_photo': 'Photo de la pièce d\'identité',
            'cnss': 'Numéro d\'assurance de travail',
            'number_carte_passport': 'Numéro de la pièce d\'identité',
        }
        widgets = {
            'iban': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: FR76 1234 5678 9123 4567 8912 345'}),
            'id_photo': forms.FileInput(attrs={'class': 'form-control-file'}),
            'cnss': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro d\'assurance'}),
            'number_carte_passport': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de carte d\'identité ou de passeport'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cnss'].required = False  # Rend le champ cnss optionnel

    def clean_iban(self):
        iban = self.cleaned_data.get('iban')
        if iban:
            iban = iban.replace(' ', '').upper()  # Nettoie et met en majuscules l'IBAN
            if len(iban) != 27 or not iban.startswith('FR'):  # Vérifie la longueur et le code pays pour un IBAN français
                raise forms.ValidationError("Veuillez entrer un IBAN français valide.")
        return iban

    def clean_id_photo(self):
        id_photo = self.cleaned_data.get('id_photo')
        if id_photo:
            if id_photo.size > 5 * 1024 * 1024:  # 5 MB
                raise forms.ValidationError("La taille de l'image ne doit pas dépasser 5 MB.")
        return id_photo
    
    
class CryptoPaymentForm(forms.Form):
    CRYPTO_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('BCH', 'Bitcoin Cash'),
        # Ajoutez d'autres cryptomonnaies supportées par BitPay selon vos besoins
    ]

    amount = forms.DecimalField(max_digits=10, decimal_places=8, min_value=0.00000001)
    crypto_currency = forms.ChoiceField(choices=CRYPTO_CHOICES)
