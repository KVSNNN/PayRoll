from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Create the first Super Admin account'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin',
                            help='Username for Super Admin (default: admin)')
        parser.add_argument('--password', type=str, default='Admin@123',
                            help='Password for Super Admin (default: Admin@123)')
        parser.add_argument('--email', type=str, default='admin@company.com',
                            help='Email for Super Admin')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists.'))
            return

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name='Super',
            last_name='Admin',
            role='SUPER_ADMIN',
            is_staff=True,
            is_superuser=True,
        )

        self.stdout.write(self.style.SUCCESS(
            f'\n[OK] Super Admin created successfully!\n'
            f'   Username: {username}\n'
            f'   Password: {password}\n'
            f'   Email: {email}\n'
            f'\n[!] Please change the password after first login.'
        ))
