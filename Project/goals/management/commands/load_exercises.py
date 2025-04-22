import json
from django.core.management.base import BaseCommand
from goals.models import Exercise
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Load or update exercises from final_accessible_exercises.json into the database'

    def handle(self, *args, **kwargs):
        with open('final_accessible_exercises.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        created_count = 0
        updated_count = 0

        for item in data:
            name = item['name']
            slug = slugify(name)

            defaults = {
                'body_part': item.get('bodyPart', ''),
                'target': item.get('target', ''),
                'equipment': item.get('equipment', ''),
                'gif_url': item.get('gifUrl', ''),
                'secondary_muscles': item.get('secondaryMuscles', []),
                'instructions': item.get('instructions', [])
            }

            try:
                obj, created = Exercise.objects.update_or_create(
                    slug=slug, defaults={**defaults, 'name': name}
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Created: {name}"))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"Updated: {name}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error with {name}: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! {created_count} created, {updated_count} updated."
        ))
