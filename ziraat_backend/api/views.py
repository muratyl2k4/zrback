from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.http import HttpResponse
from .models import Customer, Transaction
from .serializers import CustomerSerializer, TransactionSerializer
from .pdf_generator import generate_pdf

class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Customer.objects.all()
        return Customer.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            customer = request.user.customer
            return Response(self.get_serializer(customer).data)
        except Customer.DoesNotExist:
            return Response({"error": "Profil bulunamadı", "is_admin": request.user.is_superuser}, status=404)

    def perform_update(self, serializer):
        old_balance = self.get_object().balance
        instance = serializer.save()
        if instance.balance != old_balance:
            from decimal import Decimal
            diff = Decimal(str(instance.balance)) - Decimal(str(old_balance))
            instance.initial_balance += diff
            instance.save(update_fields=['initial_balance'])
            recalculate_balances(instance)

def recalculate_balances(customer):
    from decimal import Decimal
    transactions = Transaction.objects.filter(customer=customer).order_by('date', 'id')
    current_balance = customer.initial_balance
    
    for tx in transactions:
        if tx.is_incoming:
            net = tx.amount
        else:
            net = -(tx.amount + tx.mesaj_ucreti + tx.bsmv + tx.komisyon)
            
        current_balance += net
        if tx.balance_after != current_balance:
            tx.balance_after = current_balance
            tx.save(update_fields=['balance_after'])
            
    if customer.balance != current_balance:
        customer.balance = current_balance
        customer.save(update_fields=['balance'])

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Transaction.objects.all().order_by('-date', '-id')
        return Transaction.objects.filter(customer__user=self.request.user).order_by('-date', '-id')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        exploded = []
        for tx in queryset:
            date_str = timezone.localtime(tx.date).strftime("%d.%m.%Y")
            time_str = timezone.localtime(tx.date).strftime("%H:%M")
            current_balance = float(tx.balance_after)
            if tx.is_incoming:
                exploded.append({
                    "id": f"inc_{tx.id}",
                    "txId": tx.id,
                    "date": date_str,
                    "time": time_str,
                    "description": tx.description or 'Gelen Transfer',
                    "amount": float(tx.amount),
                    "color": "#22c55e",
                    "isMain": True,
                    "isIncoming": True,
                    "balance": current_balance,
                    "receipt_url": tx.receipt_file.url if tx.receipt_file else None
                })
            else:
                if float(tx.mesaj_ucreti) > 0:
                    exploded.append({
                        "id": f"msg_{tx.id}",
                        "txId": tx.id,
                        "date": date_str,
                        "time": time_str,
                        "description": "MESAJ ÜCRETİ",
                        "amount": -float(tx.mesaj_ucreti),
                        "color": "var(--text-main)",
                        "isMain": False,
                        "isIncoming": False,
                        "balance": current_balance
                    })
                    current_balance += float(tx.mesaj_ucreti)
                    
                if float(tx.bsmv) > 0:
                    exploded.append({
                        "id": f"bsmv_{tx.id}",
                        "txId": tx.id,
                        "date": date_str,
                        "time": time_str,
                        "description": "BSMV TUTARI",
                        "amount": -float(tx.bsmv),
                        "color": "var(--text-main)",
                        "isMain": False,
                        "isIncoming": False,
                        "balance": current_balance
                    })
                    current_balance += float(tx.bsmv)
                    
                if float(tx.komisyon) > 0:
                    exploded.append({
                        "id": f"kom_{tx.id}",
                        "txId": tx.id,
                        "date": date_str,
                        "time": time_str,
                        "description": "KOMİSYON ÜCRETİ",
                        "amount": -float(tx.komisyon),
                        "color": "var(--text-main)",
                        "isMain": False,
                        "isIncoming": False,
                        "balance": current_balance
                    })
                    current_balance += float(tx.komisyon)
                    
                import re
                bank_name = tx.receiver_bank or ''
                # Remove starting branch codes like "0067-" or "0067 -"
                bank_name = re.sub(r'^\d+\s*-\s*', '', bank_name).strip()
                iban = (tx.receiver_iban or '').replace(' ', '')
                
                if tx.transaction_type == 'HAVALE':
                    desc = f"{tx.receiver_name or ''} Ziraat Mobil Havale".strip()
                else:
                    desc = f"{bank_name}/{iban}-{tx.receiver_name or ''}/{tx.transaction_type}".upper() + " işlemi"
                    
                exploded.append({
                    "id": f"main_{tx.id}",
                    "txId": tx.id,
                    "date": date_str,
                    "time": time_str,
                    "description": desc,
                    "amount": -float(tx.amount),
                    "color": "var(--text-main)",
                    "isMain": True,
                    "isIncoming": False,
                    "balance": current_balance,
                    "receipt_url": tx.receipt_file.url if tx.receipt_file else None
                })
        return Response(exploded)

    def perform_create(self, serializer):
        customer = serializer.validated_data.get('customer')
        if not customer:
            customer = self.request.user.customer
            
        serializer.save(customer=customer)

    def perform_update(self, serializer):
        instance = serializer.save()

    def perform_destroy(self, instance):
        instance.delete()



    @action(detail=True, methods=['get'])
    def generate_receipt(self, request, pk=None):
        transaction = self.get_object()
        customer = transaction.customer
        
        toplam_masraf = transaction.mesaj_ucreti + transaction.bsmv + transaction.komisyon
        toplam_tutar = transaction.amount + toplam_masraf
        
        data_dict = {
            "gonderen_isim": customer.name,
            "gonderen_adres": customer.address,
            "gonderen_hesap_no": customer.account_number,
            "gonderen_iban": customer.iban,
            "gonderen_tc": customer.tc,
            "sube": customer.branch,
            "alici_banka": transaction.receiver_bank,
            "alici_sube": transaction.receiver_branch,
            "alici_iban": transaction.receiver_iban,
            "alici_hesap": transaction.receiver_account,
            "alici_isim": transaction.receiver_name,
            "tarih": timezone.localtime(transaction.date).strftime("%d.%m.%Y"),
            "saat": timezone.localtime(transaction.date).strftime("%H:%M:%S"),
            "fis_no": transaction.receipt_no,
            "tutar": f"{transaction.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "mesaj_ucreti": f"{transaction.mesaj_ucreti:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "bsmv": f"{transaction.bsmv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "komisyon": f"{transaction.komisyon:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "toplam_masraf": f"{toplam_masraf:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "toplam_tutar": f"{toplam_tutar:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "yazi_ile_tutar": transaction.amount_in_words
        }
        
        import os
        from django.conf import settings
        from django.template import Template, Context
        
        if transaction.transaction_type == 'HAVALE':
            template_name = 'havaledek.html'
        else:
            template_name = 'e-dekont (2).html'
            
        # Prioritize api/templates directory if it exists, otherwise fallback to base dir
        template_path_new = os.path.join(settings.BASE_DIR, 'api', 'templates', template_name)
        if os.path.exists(template_path_new):
            template_path = template_path_new
        else:
            template_path = os.path.join(settings.BASE_DIR, '..', '..', template_name)
            
        template_path = os.path.abspath(template_path)
        
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        template = Template(html_content)
        rendered_html = template.render(Context(data_dict))
        
        return HttpResponse(rendered_html, content_type='text/html')

    @action(detail=True, methods=['patch'])
    def upload_receipt(self, request, pk=None):
        transaction = self.get_object()
        receipt_file = request.FILES.get('receipt_file')
        if receipt_file:
            if transaction.receipt_file:
                transaction.receipt_file.delete(save=False)
            transaction.receipt_file = receipt_file
            transaction.save(update_fields=['receipt_file'])
            return Response({"status": "success", "url": transaction.receipt_file.url})
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def generate_statement(self, request):
        days = request.query_params.get('days')
        customer = request.user.customer
        
        queryset = self.get_queryset()
        if days:
            from datetime import timedelta
            start_date = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(date__gte=start_date)
            
        # Re-sort chronologically for the statement, as the statement script expects chronological order.
        # But wait, the standard statement format usually lists the oldest or newest first?
        # generate_statement defaults have oldest at the bottom, newest at the top.
        # So we keep '-date', '-id' ordering.
        
        # Build statement_data
        statement_data = {
            "customer": {
                "name": customer.name,
                "address": customer.address
            },
            "account": {
                "branch": customer.branch,
                "number": customer.account_number,
                "iban": customer.iban,
                "currency": "TRY",
                "period": "" # we can leave it empty or format it
            },
            "transactions": []
        }
        
        total_debit = 0.0
        total_credit = 0.0
        
        # If there are transactions, calculate the period
        if queryset.exists():
            first_tx = queryset.last() # Because it's descending order, last() is the oldest
            last_tx = queryset.first()
            if first_tx and last_tx:
                period_str = f"{timezone.localtime(first_tx.date).strftime('%d.%m.%Y')}-{timezone.localtime(last_tx.date).strftime('%d.%m.%Y')}"
                statement_data["account"]["period"] = period_str
                
        for tx in queryset:
            date_str = timezone.localtime(tx.date).strftime("%d.%m.%Y")
            current_balance = float(tx.balance_after)
            
            # Reconstruct the exploded transactions
            if tx.is_incoming:
                total_credit += float(tx.amount)
                statement_data["transactions"].append({
                    "date": date_str,
                    "receipt_no": tx.receipt_no or "",
                    "description": tx.description or 'Gelen Transfer',
                    "amount": f"{tx.amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    "balance": f"{current_balance:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                })
            else:
                import re
                bank_name = tx.receiver_bank or ''
                bank_name = re.sub(r'^\d+\s*-\s*', '', bank_name).strip()
                iban = (tx.receiver_iban or '').replace(' ', '')
                
                if tx.transaction_type == 'HAVALE':
                    desc = f"{tx.receiver_name or ''} Ziraat Mobil Havale".strip()
                else:
                    desc = f"{bank_name}/{iban}-{tx.receiver_name or ''}/{tx.transaction_type}".upper() + " işlemi"
                
                
                total_debit += float(tx.amount)
                # Main
                statement_data["transactions"].append({
                    "date": date_str,
                    "receipt_no": tx.receipt_no or "",
                    "description": desc,
                    "amount": f"-{tx.amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    "balance": f"{current_balance:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                })
                
                # Fees (in reverse order to match the list explosion we had, or chronological?)
                # Actually, in generate_statement_data, we should process fees backwards from current_balance?
                # The generate_statement.py script takes them exactly as provided.
                # Let's just explode them.
                cb = current_balance
                if float(tx.komisyon) > 0:
                    cb += float(tx.komisyon)
                    total_debit += float(tx.komisyon)
                    statement_data["transactions"].append({
                        "date": date_str,
                        "receipt_no": (tx.receipt_no[:-1] + "1") if tx.receipt_no else "",
                        "description": "KOMİSYON ÜCRETİ",
                        "amount": f"-{tx.komisyon:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                        "balance": f"{cb:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    })
                if float(tx.bsmv) > 0:
                    cb += float(tx.bsmv)
                    total_debit += float(tx.bsmv)
                    statement_data["transactions"].append({
                        "date": date_str,
                        "receipt_no": (tx.receipt_no[:-1] + "2") if tx.receipt_no else "",
                        "description": "BSMV TUTARI",
                        "amount": f"-{tx.bsmv:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                        "balance": f"{cb:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    })
                if float(tx.mesaj_ucreti) > 0:
                    cb += float(tx.mesaj_ucreti)
                    total_debit += float(tx.mesaj_ucreti)
                    statement_data["transactions"].append({
                        "date": date_str,
                        "receipt_no": (tx.receipt_no[:-1] + "3") if tx.receipt_no else "",
                        "description": "MESAJ ÜCRETİ",
                        "amount": f"-{tx.mesaj_ucreti:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                        "balance": f"{cb:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    })
                    
        statement_data["totals"] = {
            "debit": f"-{total_debit:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            "credit": f"{total_credit:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        }
                    
        # Generate the PDF
        from . import generate_statement
        import time
        import os
        from django.conf import settings
        from django.core.files.base import ContentFile
        
        pdf_filename = f"Hesap_Hareketleri_{timezone.now().strftime('%d%m%Y')}.pdf"
        temp_pdf_path = os.path.join(settings.MEDIA_ROOT, f"temp_{int(time.time())}.pdf")
        
        # Ensure media root exists
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        # Generate
        generate_statement.generate_pdf(statement_data, temp_pdf_path)
        
        # We can serve it directly using FileResponse
        from django.http import FileResponse
        response = FileResponse(open(temp_pdf_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
        return response
