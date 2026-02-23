import json
import os
from django.core.management.base import BaseCommand
from your_app.models import BMADTemplate

class Command(BaseCommand):
    help = 'Imports a library of BMAD v6 templates from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the library.json file')

    def handle(self, *args, **options):
        path = options['file_path']
        if not os.path.exists(path):
            self.stderr.write(f"File not found: {path}")
            return

        with open(path, 'r') as f:
            data = json.load(f)

        for item in data:
            template, created = BMADTemplate.objects.get_or_create(
                name=item['name'],
                defaults={'sections': item['sections'], 'is_agent': item.get('is_agent', True)}
            )
            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{status} template: {template.name}"))