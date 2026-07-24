import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ziraat_backend.settings')
django.setup()

from django.contrib.auth.models import User

# Check if murat exists, if not create superuser
if not User.objects.filter(username='murat').exists():
    User.objects.create_superuser('murat', 'murat@ziraat.com', 'muratyl1A')
    print("Admin kullanicisi murat basariyla olusturuldu.")
else:
    u = User.objects.get(username='murat')
    u.set_password('muratyl1A')
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print("Admin kullanicisi murat güncellendi.")
