"""Management command to load exercises from JSON into the database."""
# pylint: disable=E1101,unused-argument

import json

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.utils.text import slugify

from goals.models import Exercise


class Command(BaseCommand):
    """Load exercises from final_accessible_exercises.json into the database."""
    help = 'Load exercises from final_accessible_exercises.json into the database'

    def handle(self, *args, **options):
        """Entry point for loading exercises."""
        try:
            with open('final_accessible_exercises.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except OSError as e:
            self.stderr.write(self.style.ERROR(f"Error reading JSON file: {e}"))
            return

        count = 0
        for item in data:
            try:
                Exercise.objects.create(
                    name=item['name'],
                    slug=slugify(item['name']),
                    body_part=item.get('bodyPart', ''),
                    target=item.get('target', ''),
                    equipment=item.get('equipment', ''),
                    gif_url=item.get('gifUrl', ''),
                    secondary_muscles=item.get('secondaryMuscles', []),
                    instructions=item.get('instructions', [])
                )
                count += 1
                self.stdout.write(self.style.SUCCESS(f"Loaded: {item['name']}"))
            except IntegrityError as e:
                self.stderr.write(self.style.ERROR(f"Integrity error for {item['name']}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Done! {count} exercises loaded."))
