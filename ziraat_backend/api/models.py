from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import os

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    account_number = models.CharField(max_length=20)
    iban = models.CharField(max_length=100)
    tc = models.CharField(max_length=11, default="11111111111")
    branch = models.CharField(max_length=100, default="0010/İSKENDERUN/HATAY ŞUBESİ")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

def receipt_upload_path(instance, filename):
    # media/username/2026-07-24/dekont_F12345.pdf
    username = instance.customer.user.username if instance.customer.user else 'unknown'
    date_str = timezone.localtime(instance.date).strftime('%Y-%m-%d')
    return os.path.join(username, date_str, filename)

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('FAST', 'FAST işlemi'),
        ('HAVALE', 'Havale işlemi'),
        ('EFT', 'EFT işlemi')
    ]

    customer = models.ForeignKey(Customer, related_name='transactions', on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    receipt_no = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_in_words = models.CharField(max_length=255, default="", blank=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Fees
    mesaj_ucreti = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bsmv = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    komisyon = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Receiver info (Optional for incoming)
    receiver_bank = models.CharField(max_length=100, blank=True, null=True)
    receiver_iban = models.CharField(max_length=100, blank=True, null=True)
    receiver_name = models.CharField(max_length=100, blank=True, null=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='FAST')
    is_incoming = models.BooleanField(default=False)
    receipt_file = models.FileField(upload_to=receipt_upload_path, null=True, blank=True)

    def __str__(self):
        return f"{self.receipt_no} - {self.description}"

