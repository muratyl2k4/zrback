import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ziraat_backend.settings')
django.setup()

from api.models import Customer, Transaction

# Create Samet Dindar
customer, created = Customer.objects.get_or_create(
    name="SAMET DİNDAR",
    defaults={
        "address": "YENİŞEHİR MAH. 27. SK NO 2 31200 İSKENDERUN HATAY",
        "account_number": "9305790-5001",
        "iban": "TR760001009010093057905001",
        "balance": 59400.56
    }
)

# Create the transaction to Muhammed Tunç
transaction, t_created = Transaction.objects.get_or_create(
    receipt_no="F04522",
    defaults={
        "customer": customer,
        "description": "AKBANK T.A.Ş./TR520004600215888000258987-MUHAMMED TUNÇ/FAST işlemi",
        "amount": 12000.00,
        "amount_in_words": "ONİKİ BİN TÜRK LİRASI",
        "balance_after": 59408.93,
        "receiver_bank": "0067 - AKBANK T.A.Ş.",
        "receiver_iban": "TR52 0004 6002 1588 8000 2589 87",
        "receiver_name": "MUHAMMED TUNÇ",
        "transaction_type": "FAST"
    }
)

print(f"Customer created/exists: {customer.name}")
print(f"Transaction created/exists: {transaction.receipt_no}")
