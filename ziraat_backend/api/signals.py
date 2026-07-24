from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Transaction

@receiver(post_save, sender=Transaction)
def transaction_post_save(sender, instance, created, **kwargs):
    # Only recalculate if we are not already inside a recalculation
    # To prevent recursion, we can check if update_fields is exactly ['balance_after'] or ['receipt_file']
    if kwargs.get('update_fields') and (
        set(kwargs.get('update_fields')) == {'balance_after'} or 
        set(kwargs.get('update_fields')) == {'receipt_file'}
    ):
        return
        
    from .views import recalculate_balances
    recalculate_balances(instance.customer)

@receiver(post_delete, sender=Transaction)
def transaction_post_delete(sender, instance, **kwargs):
    from .views import recalculate_balances
    recalculate_balances(instance.customer)
