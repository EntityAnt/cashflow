from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Создает суперпользователя admin с паролем 1234"

    def handle(self, *args, **options):
        username = "admin"
        password = "1234"
        email = "admin@example.com"

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"Пользователь '{username}' уже существует")
            )
            return

        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Создан суперпользователь:\n"
                    f"Имя: {username}\n"
                    f"Пароль: {password}\n"
                    f"Email: {email}"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при создании пользователя: {str(e)}")
            )
