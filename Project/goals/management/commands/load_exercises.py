import json
from django.core.management.base import BaseCommand
from goals.models import Exercise
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Load exercises from final_accessible_exercises.json into the database'

    def handle(self, *args, **kwargs):
        with open('final_accessible_exercises.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

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
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error with {item['name']}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone! {count} exercises loaded."))
