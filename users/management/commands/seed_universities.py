import json
from pathlib import Path

from django.core.management.base import BaseCommand

from users.models import University


class Command(BaseCommand):
    help = 'Seed universities from fixtures/universities.json'

    def handle(self, *args, **options):
        fixtures_path = Path(__file__).resolve().parent.parent.parent / 'fixtures' / 'universities.json'
        with open(fixtures_path, encoding='utf-8') as f:
            data = json.load(f)

        created = 0
        for item in data:
            _, was_created = University.objects.get_or_create(
                email_domain=item['email_domain'],
                defaults={'name': item['name']},
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Done. Created {created} new universities.'))
