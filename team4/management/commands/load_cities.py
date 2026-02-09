from django.core.management.base import BaseCommand
from team4.models import City, Province
from team4.fields import Point
import json

class Command(BaseCommand):
    help = 'Load cities with location data'

    def handle(self, *args, **options):
        fixture_path = 'team4/fixtures/cities.json'
        
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        updated_count = 0
        created_count = 0
        skipped_count = 0
        
        for item in data:
            city_id = item['city_id']
            name_fa = item['name_fa']
            name_en = item['name_en']
            
            # --- FIX: Get province_id from nested 'province' object ---
            province_data = item.get('province', {})
            p_id = province_data.get('province_id')
            
            try:
                province = Province.objects.using('team4').get(province_id=p_id)
            except Province.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠ استان {p_id} برای شهر {name_fa} یافت نشد'))
                skipped_count += 1
                continue
            
            # --- FIX: Get latitude/longitude from nested 'location' object ---
            location = None
            loc_data = item.get('location', {})
            if loc_data.get('latitude') and loc_data.get('longitude'):
                lat = float(loc_data['latitude'])
                lng = float(loc_data['longitude'])
                location = Point(lng, lat)
            
            # Update or Create logic
            try:
                city = City.objects.using('team4').get(city_id=city_id)
                city.name_fa = name_fa
                city.name_en = name_en
                city.province = province
                city.location = location
                # Only save relevant fields
                city.save(using='team4', update_fields=['name_fa', 'name_en', 'province', 'location', 'updated_at'])
                updated_count += 1
            except City.DoesNotExist:
                city = City(
                    city_id=city_id,
                    name_fa=name_fa,
                    name_en=name_en,
                    province=province,
                    location=location
                )
                city.save(using='team4')
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ کامل شد: {created_count} ایجاد، {updated_count} بروزرسانی، {skipped_count} رد شد'
        ))