from django.core.management.base import BaseCommand
from team4.models import City, Province, Village

class Command(BaseCommand):
    help = 'Show database statistics for Provinces, Cities, and Villages'

    def handle(self, *args, **options):
        # Fetching counts from the 'team4' database
        province_count = Province.objects.using('team4').count()
        city_count = City.objects.using('team4').count()
        village_count = Village.objects.using('team4').count()
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 آمار دیتابیس (MySQL):'))
        self.stdout.write(f'  ✓ تعداد استان‌ها: {province_count}')
        self.stdout.write(f'  ✓ تعداد شهرها: {city_count}')
        self.stdout.write(f'  ✓ تعداد روستاها: {village_count}')
        
        # Display Sample Cities
        if city_count > 0:
            self.stdout.write(self.style.MIGRATE_LABEL(f'\n📍 نمونه شهرها:'))
            cities = City.objects.using('team4').select_related('province')[:5]
            for city in cities:
                location_str = f'({city.longitude}, {city.latitude})' if city.location else 'بدون موقعیت'
                self.stdout.write(f'  • {city.name_fa} ({city.province.name_fa}) - مختصات: {location_str}')

        # Display Sample Villages
        if village_count > 0:
            self.stdout.write(self.style.MIGRATE_LABEL(f'\n🏡 نمونه روستاها:'))
            # Using select_related for city to avoid multiple DB hits (N+1 problem)
            villages = Village.objects.using('team4').select_related('city')[:5]
            for village in villages:
                location_str = f'({village.longitude}, {village.latitude})' if village.location else 'بدون موقعیت'
                self.stdout.write(f'  • {village.name_fa} (شهر: {village.city.name_fa}) - مختصات: {location_str}')
        
        if province_count == 0 and city_count == 0 and village_count == 0:
            self.stdout.write(self.style.WARNING('\n⚠ دیتابیس خالی است. ابتدا دستورات load را اجرا کنید.'))