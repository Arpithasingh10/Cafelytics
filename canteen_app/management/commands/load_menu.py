from django.core.management.base import BaseCommand
from canteen_app.utils.excel_io import load_menu_df
from canteen_app.models import Category, MenuItem

class Command(BaseCommand):
    help = "Load menu from Excel into DB (idempotent)"

    def handle(self, *args, **options):
        df = load_menu_df()
        for _, row in df.iterrows():
            cat, _ = Category.objects.get_or_create(name=row.get('Category','Other'))
            mi, created = MenuItem.objects.update_or_create(
                itemid=row['ItemID'],
                defaults={
                    'name': row['ItemName'],
                    'category': cat,
                    'type': row.get('Type','Veg'),
                    'portion': row.get('Portion',''),
                    'availability': row.get('Availability','All Day'),
                    'price': float(row.get('Price',0.0)),
                    'preference_score': float(row.get('PreferenceScore',0.0)),
                    'active': True,
                    'remarks': row.get('Remarks','')
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {mi}"))
        self.stdout.write(self.style.SUCCESS("Menu load complete."))
