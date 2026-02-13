from django.core.management.base import BaseCommand
from team4.models import Facility, City, Category, Amenity
from team4.fields import Point
import json
import os

class Command(BaseCommand):
    help = 'Load restaurants from iran_restaurants_complete.json'

    def handle(self, *args, **options):
        # Path to the file
        fixture_path = 'team4/fixtures/restaurants.json'
        
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f'❌ File not found: {fixture_path}'))
            return

        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        # Ensure the 'Restaurant' category exists (ID 1)
        # We try to get it, or create it if missing to prevent errors
        category_obj, _ = Category.objects.using('team4').get_or_create(
            category_id=1,
            defaults={
                'name_fa': 'رستوران',
                'name_en': 'Restaurant',
                'marker_color': 'orange'
            }
        )

        total_items = len(data)
        self.stdout.write(f"🚀 Starting import of {total_items} restaurants...")

        for index, item in enumerate(data):
            # 1. Handle ID
            fac_id = item.get('id') or item.get('facility_id')
            
            # 2. Handle Foreign Key: City
            city_id = item.get('city_id')
            try:
                city_obj = City.objects.using('team4').get(city_id=city_id)
            except City.DoesNotExist:
                # self.stdout.write(self.style.WARNING(f'⚠ City ID {city_id} not found. Skipping restaurant {item.get("name_en")}.'))
                skipped_count += 1
                continue

            # 3. Handle Location
            location = None
            loc_data = item.get('location', {})
            if loc_data.get('latitude') and loc_data.get('longitude'):
                lat = float(loc_data['latitude'])
                lng = float(loc_data['longitude'])
                location = Point(lng, lat)
            
            # 4. Handle Foreign Key: Category
            # The JSON has 'category_id', usually 1
            cat_id = item.get('category_id', 1)
            if cat_id != category_obj.category_id:
                try:
                    category_obj = Category.objects.using('team4').get(category_id=cat_id)
                except Category.DoesNotExist:
                    # Fallback to default restaurant category
                    pass

            # Prepare data dictionary
            defaults = {
                'name_fa': item.get('name_fa'),
                'name_en': item.get('name_en'),
                'category': category_obj,
                'city': city_obj,
                'address': item.get('address', ''),
                'location': location,
                'phone': item.get('phone', ''),
                'email': item.get('email', ''),
                'website': item.get('website', ''),
                'description_fa': item.get('description_fa', ''),
                'description_en': item.get('description_en', ''),
                'avg_rating': item.get('avg_rating', 0.0),
                'review_count': item.get('review_count', 0),
                'status': item.get('status', True),
                'is_24_hour': item.get('is_24_hour', False),
                'price_tier': item.get('price_tier', 'unknown'),
            }

            # 5. Create or Update Facility
            try:
                facility = Facility.objects.using('team4').get(fac_id=fac_id)
                
                # Update fields
                for key, value in defaults.items():
                    setattr(facility, key, value)
                
                facility.save(using('team4'))
                updated_count += 1
                
            except Facility.DoesNotExist:
                # Create new
                facility = Facility(fac_id=fac_id, **defaults)
                facility.save(using='team4')
                created_count += 1

            # 6. Handle Many-to-Many: Amenities
            # The JSON has a list of IDs: "amenities": [1, 5, 8]
            amenity_ids = item.get('amenities', [])
            if amenity_ids:
                # Fetch valid amenities objects
                valid_amenities = Amenity.objects.using('team4').filter(amenity_id__in=amenity_ids)
                # Set the relationship (clears old ones, adds new ones)
                facility.amenities.set(valid_amenities)

            # Progress log every 100 items
            if (index + 1) % 100 == 0:
                self.stdout.write(f"   Processed {index + 1}/{total_items}...")

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Complete: {created_count} Created, {updated_count} Updated, {skipped_count} Skipped.'
        ))