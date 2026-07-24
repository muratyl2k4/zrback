from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from .models import Customer

@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_user(request):
    data = request.data
    try:
        user = User.objects.create_user(
            username=data['username'],
            password=data['password']
        )
        
        Customer.objects.create(
            user=user,
            name=data['name'],
            tc=data.get('tc', '11111111111'),
            iban=data['iban'],
            account_number=data.get('account_number', ''),
            branch=data.get('branch', '0010/İSKENDERUN/HATAY ŞUBESİ'),
            balance=data.get('balance', 0.00),
            initial_balance=data.get('balance', 0.00),
            address=data.get('address', '')
        )
        return Response({"message": "Kullanıcı başarıyla oluşturuldu!"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
