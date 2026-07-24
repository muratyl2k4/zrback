from rest_framework import serializers
from .models import Customer, Transaction

class CustomerSerializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['user']

    def get_is_admin(self, obj):
        return obj.user.is_superuser if obj.user else False

class TransactionSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), required=False)
    
    class Meta:
        model = Transaction
        fields = '__all__'
