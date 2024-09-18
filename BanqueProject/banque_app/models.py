import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('other', 'Autre')
    ]
    PROFESSION_CHOICES = [
        ('employed', 'Employé'),
        ('self-employed', 'Entrepreneur'),
        ('retired', 'Retraité'),
        ('other', 'Autre')
    ]
    STATUT_CHOICES = [
        ('Vérifier', 'Vérifier'),
        ('Non vérifier', 'Non vérifier'),
        ('En attente de vérification', 'En attente de vérification'),
        ('En cours de vérification', 'En cours de vérification'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birth_date = models.DateField(null=True, blank=True)
    birth_place = models.CharField(max_length=255)
    nationality = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    income_source = models.CharField(max_length=255, null=True, blank=True)  # Made optional
    profession = models.CharField(max_length=20, choices=PROFESSION_CHOICES)
    terms = models.BooleanField(default=False)  # BooleanFields don't need null=True
    consent = models.BooleanField(default=False)
    confirmation = models.BooleanField(default=False)
    statut = models.CharField(max_length=30, choices=STATUT_CHOICES, default='Non vérifier')

    def __str__(self):
        return self.user.username
    
    
class Identite(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    iban = models.CharField(max_length=34)
    id_photo = models.ImageField(upload_to='user_photos/')
    cnss = models.CharField(max_length=100,null=True)
    number_carte_passport = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.user.username} - {self.cnss}"


class DemandePret(models.Model):
    # L'utilisateur qui fait la demande de prêt
    utilisateur = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='demandes_pret')

    # Montant demandé pour le prêt
    montant_demande = models.DecimalField(max_digits=15, decimal_places=2)

    # Durée du prêt en mois
    duree = models.PositiveIntegerField(help_text="Durée en mois")

    # Taux d'intérêt annuel applicable au prêt
    taux_interet = models.DecimalField(max_digits=5, decimal_places=2, help_text="Taux d'intérêt annuel en pourcentage")

    # Objet ou motif de la demande de prêt
    motif = models.TextField()

    # Date de la demande de prêt
    date_demande = models.DateTimeField(auto_now_add=True)

    # Statut de la demande de prêt
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('APPROUVE', 'Approuvé'),
        ('REFUSE', 'Refusé'),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')

    paiement_effectue = models.BooleanField(default=False)

    # Commentaires ou remarques de la banque (facultatif)
    commentaires_banque = models.TextField(null=True, blank=True,default="Votre demende est en cours d'examen...")

    def __str__(self):
        return f"Demande de prêt de {self.montant_demande} EUR "

    class Meta:
        verbose_name = "Demande de Prêt"
        verbose_name_plural = "Demandes de Prêts"

    

class CrediteCompte(models.Model):
    # L'utilisateur auquel le crédit est destiné
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credits')

    # Numéro de compte pour le crédit
    numero_compte = models.CharField(max_length=34)  # Inclut l'IBAN ou seulement le numéro de compte selon le besoin

    # Montant à créditer
    montant = models.DecimalField(max_digits=10, decimal_places=2)

    # Devise utilisée pour la transaction
    devise = models.CharField(max_length=3, default='EUR')  # EUR par défaut, mais peut être modifié

    # Référence unique de la transaction
    reference_transaction = models.CharField(max_length=100, unique=True)

    # Description ou motif de la transaction
    description = models.TextField(null=True, blank=True)

    # Date de la transaction
    date_transaction = models.DateTimeField(auto_now_add=True)

    # Émetteur du crédit (facultatif)
    emetteur = models.CharField(max_length=255, null=True, blank=True)


    def __str__(self):
        return f"Crédit de {self.montant} {self.devise} sur le compte {self.numero_compte}"

    class Meta:
        verbose_name = "Crédit de Compte"
        verbose_name_plural = "Crédits de Comptes"


class Virement(models.Model):
    STATUT_CHOICES = [
        (1, 'Initié'),
        (2, 'En cours'),
        (3, 'Terminé')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)
    statut = models.IntegerField(choices=STATUT_CHOICES, default=1)
    message_admin = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Virement de {self.montant} EUR pour {self.user.username} - Statut: {dict(self.STATUT_CHOICES).get(self.statut)}"

    class Meta:
        verbose_name = "Virement"
        verbose_name_plural = "Virements"


class CompteBancaire(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    numero_compte = models.CharField(max_length=20, unique=True)
    solde = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Compte {self.numero_compte} de {self.user.user.last_name}"
    

class DemandeRetrait(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demandes_retrait')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Demande de retrait de {self.amount} € par {self.user.username}"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    recipients = models.ManyToManyField(UserProfile, related_name='received_messages')
    subject = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    no_reply = models.BooleanField(default=True)  # New field to indicate no-reply messages

    def __str__(self):
        return f"Message from {self.sender} - {self.subject}"


class Attachment(models.Model):
    message = models.ForeignKey(Message, related_name='attached_files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='message_attachments/')
    

class UserPayment(models.Model):

    app_user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    payment_bool = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=500, blank=True, null=True)
    demande_pret = models.OneToOneField(DemandePret, on_delete=models.CASCADE)

    def __str__(self):
        return f"Statut de paiement pour {self.app_user.user.username} - Demande de prêt: {self.demande_pret.id}"



class PaymentHistory(models.Model):
    user_payment = models.ForeignKey(UserPayment, on_delete=models.CASCADE, related_name='payment_history')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('SUCCESS', 'Succès'),
        ('FAILURE', 'Échec'),
        ('PENDING', 'En attente')
    ])
    stripe_payment_intent_id = models.CharField(max_length=500, blank=True, null=True)
    stripe_checkout_session_id = models.CharField(max_length=500, blank=True, null=True)
    failure_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Paiement {self.status} de {self.amount} pour {self.user_payment.app_user.user.username} le {self.timestamp}"


class CryptoPayment(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('paid', 'Paid'),
        ('confirmed', 'Confirmed'),
        ('complete', 'Complete'),
        ('expired', 'Expired'),
        ('invalid', 'Invalid'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=8)
    crypto_currency = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    bitpay_invoice_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} - {self.amount} {self.crypto_currency}"
