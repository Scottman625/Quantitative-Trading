from django.conf import settings
from django.core.management.base import BaseCommand
from stockCore.models import User

class Command(BaseCommand):

    def handle(self, *args, **options):
        if User.objects.filter(email="admin@mysite.com").count() == 0:
            for user in settings.ADMINS:
                name = user[0].replace(' ', '')
                email = user[1]
                password = 'admin'
                print('Creating account for %s (%s)' % (name, email))
                admin = User.objects.create_superuser(email=email, name=name, password=password)
                admin.save()
        else:
            print('Admin accounts can only be initialized if no Accounts exist')