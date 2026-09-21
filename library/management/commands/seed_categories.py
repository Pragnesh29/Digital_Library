from django.core.management.base import BaseCommand
from library.models import Category

class Command(BaseCommand):
    help = 'Seeds initial categories (Defence, Research)'

    def handle(self, *args, **options):
        cats = ['Defence', 'Research']
        for name in cats:
            obj, created = Category.objects.get_or_create(
                name=name,
                defaults={'target_type': 'both'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Category '{name}' created successfully."))
            else:
                self.stdout.write(f"Category '{name}' already exists.")
