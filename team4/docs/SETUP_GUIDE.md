# 🚀 Team 4 Backend Setup Guide

## Project Overview

**Team 4** is responsible for implementing the **Geolocation-Based Facility Management System** for the BugOff travel application. This backend provides APIs for managing and querying facilities (hotels, restaurants, hospitals, museums) across Iran with advanced geolocation features.

### Key Features

- ✅ **Geolocation Support**: Custom MySQL POINT field implementation without GeoDjango
- ✅ **Comprehensive Database**: 31 provinces and 1112 cities with coordinates
- ✅ **Smart Search**: Find facilities by location, category, rating, and amenities
- ✅ **Distance Calculations**: Haversine formula for accurate distance computation
- ✅ **Nearby Search**: Find facilities within configurable radius
- ✅ **Facility Comparison**: Compare multiple facilities side-by-side
- ✅ **RESTful APIs**: Clean, paginated, filtered endpoints

---

## Technology Stack

### Core Framework
- **Django 4.2.27**: Web framework
- **Django REST Framework**: API development
- **MySQL 8.0+**: Spatial database with POINT support

### Key Libraries
- `djangorestframework`: REST API toolkit
- `django-filter`: Advanced filtering
- `mysqlclient`: MySQL database adapter
- `Pillow`: Image processing
- `requests`: HTTP client

### Custom Components
- **PointField**: Custom model field for MySQL POINT type
- **FacilityService**: Business logic layer
- **Management Commands**: Data loading utilities

---

## System Requirements

### Prerequisites

- **Python**: 3.10+
- **MySQL Server**: 8.0+
- **Git**: For version control
- **PowerShell**: For Windows command execution

### Hardware
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for package installation

---

## Installation Guide

### Step 1: Clone Repository

```powershell
cd e:\alirreza\cds\uni\SE\project\BugOff\Software-Engineering-1404-01_G2
```

### Step 2: Install Dependencies

```powershell
# Install all required packages
pip install -r requirements.txt

# Or install individually:
pip install djangorestframework django-filter mysqlclient Pillow requests
```

**Verify installation:**
```powershell
pip list | Select-String "django"
```

Expected output:
```
Django                    4.2.27
djangorestframework       3.14.0
django-filter            23.5
```

### Step 3: Database Setup

#### A. Create MySQL Database

Open MySQL Workbench or MySQL CLI and execute:

```sql
CREATE DATABASE IF NOT EXISTS team4_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Verify creation
SHOW DATABASES LIKE 'team4_db';
```

#### B. Configure Environment Variables

Create or update `.env` file in project root:

```env
# Team 4 Database Configuration
TEAM4_DATABASE_URL=mysql://root:YOUR_MYSQL_PASSWORD@localhost:3306/team4_db
```

**Important**: Replace `YOUR_MYSQL_PASSWORD` with your actual MySQL root password.

#### C. Apply Database Migrations

```powershell
# Generate migration files
python manage.py makemigrations team4

# Apply migrations to team4 database
python manage.py migrate --database=team4

# Verify tables created
python manage.py dbshell --database=team4
# Then in MySQL: SHOW TABLES;
```

Expected tables:
- `facilities_province`
- `facilities_city`
- `facilities_category`
- `facilities_amenity`
- `facilities_facility`
- `facilities_facility_amenity`
- `facilities_pricing`
- `facilities_image`

### Step 4: Load Initial Data

#### A. Load Provinces (31 records)

```powershell
python manage.py load_provinces
```

Expected output:
```
✓ ایجاد: آذربایجان شرقی
✓ ایجاد: آذربایجان غربی
...
✅ کامل شد: 31 ایجاد، 0 بروزرسانی
```

#### B. Load Cities (1112 records)

```powershell
python manage.py load_cities
```

Expected output:
```
... 500 شهر ایجاد شد
... 1000 شهر ایجاد شد
✅ کامل شد: 1112 ایجاد، 0 بروزرسانی، 0 رد شد
```

```powershell
python manage.py load_villages
```
Expected output:
```
✅ Done: 20417 villages created, 0 skipped
```
```powershell
python manage.py load_amenity
```
```powershell
python manage.py load_category
```
```powershell
python manage.py load_hotels
```
‍‍‍```powershell
python manage.py load_hospitals
```



**Note**: This process takes 2-3 minutes due to 1112 database inserts with geolocation data.

#### C. Verify Data Loading

```powershell
python manage.py show_stats
```

Expected output:
```

📊 آمار دیتابیس (MySQL):
  ✓ تعداد استان‌ها: 31
  ✓ تعداد شهرها: 707
  ✓ تعداد روستاها: 20417

📍 نمونه شهرها:
  • آبیش احمد (آذربایجان شرقی) - مختصات: (47.3169755, 39.0431974)
  • عجب‌ شیر (آذربایجان شرقی) - مختصات: (45.8936922, 37.4770929)
  • آق کند (آذربایجان شرقی) - مختصات: (48.0648621, 37.2575571)
  • آذرشهر (آذربایجان شرقی) - مختصات: (45.9781014, 37.7576638)
  • بخشایش (آذربایجان شرقی) - مختصات: (46.9471214, 38.131648)

🏡 نمونه روستاها:
  • کش (شهر: تهران) - مختصات: (50.6323169, 36.2167746)
  • کشار علیا (شهر: تهران) - مختصات: (51.2308379, 35.8144568)
  • کشار سفلی (شهر: تهران) - مختصات: (51.2437218, 35.8098696)
  • کیگا (شهر: تهران) - مختصات: (51.3102586, 35.8609118)
  • پس قلعه (شهر: تهران) - مختصات: (51.4233411, 35.836195)
```

### Step 5: Create Superuser

```powershell
python manage.py createsuperuser
```

Enter the following credentials:
- **Username**: admin
- **Email**: admin@example.com  
- **Password**: admin123 (or your preferred password)

### Step 6: Start Development Server

```powershell
python manage.py runserver
```

Server should start at: http://127.0.0.1:8000/

**Access points:**
- Django Admin: http://localhost:8000/admin/
- API Root: http://localhost:8000/team4/api/
- Browsable API: Available for all endpoints

---

## API Reference

### Base URL

```
http://localhost:8000/team4/api/
```

### Authentication

Currently using session authentication (Django Admin login). For production, implement JWT or Token authentication via Core app.

### Endpoints

#### 1. Provinces API

**List all provinces**
```http
GET /api/provinces/
```

**Response:**
```json
[
  {
    "province_id": 1,
    "name_fa": "آذربایجان شرقی",
    "name_en": "East Azarbaijan",
    "latitude": 37.9035733,
    "longitude": 46.2682109
  },
  ...
]
```

**Get single province**
```http
GET /api/provinces/{id}/
```

#### 2. Cities API

**List all cities**
```http
GET /api/cities/
```

**Filter by province**
```http
GET /api/cities/?province=Tehran
```

**Response:**
```json
[
  {
    "city_id": 789,
    "name_fa": "تهران",
    "name_en": "Tehran",
    "province": {
      "province_id": 8,
      "name_fa": "تهران",
      "name_en": "Tehran"
    },
    "latitude": 35.6892523,
    "longitude": 51.3896004
  },
  ...
]
```

#### 3. Categories API

**List all categories**
```http
GET /api/categories/
```

**Response:**
```json
[
  {
    "category_id": 1,
    "name_fa": "هتل",
    "name_en": "Hotel",
    "is_emergency": false,
    "marker_color": "blue"
  },
  ...
]
```

#### 4. Amenities API

**List all amenities**
```http
GET /api/amenities/
```

#### 5. Facilities API

**List facilities with filters**
```http
GET /api/facilities/?city=Tehran&category=Hotel&min_rating=4
```

**Query Parameters:**
- `city`: City name (Persian or English)
- `category`: Category name
- `min_rating`: Minimum rating (0-5)
- `max_rating`: Maximum rating (0-5)
- `min_price`: Minimum price
- `max_price`: Maximum price
- `amenities`: Comma-separated amenity IDs
- `is_24_hour`: Boolean (true/false)
- `sort`: rating | review_count | distance
- `page`: Page number
- `page_size`: Results per page (default: 10, max: 100)

**Response:**
```json
{
  "count": 25,
  "next": "http://localhost:8000/team4/api/facilities/?page=2",
  "previous": null,
  "results": [
    {
      "fac_id": 1,
      "name_fa": "هتل اسپیناس",
      "name_en": "Espinas Hotel",
      "category": "Hotel",
      "city": "Tehran",
      "latitude": 35.7219,
      "longitude": 51.4157,
      "avg_rating": 4.5,
      "review_count": 120,
      "min_price": 5000000
    },
    ...
  ]
}
```

**Get facility details**
```http
GET /api/facilities/{id}/
```

**Response includes:**
- Full facility information
- All images
- All pricing options
- All amenities
- Province and city details

**Find nearby facilities**
```http
GET /api/facilities/{id}/nearby/?radius=5&category=Restaurant
```

**Query Parameters:**
- `radius`: Search radius in kilometers (default: 5)
- `category`: Filter by category (optional)

**Response:**
```json
{
  "center": {
    "fac_id": 1,
    "name_fa": "هتل اسپیناس",
    ...
  },
  "radius_km": 5,
  "count": 15,
  "nearby_facilities": [
    {
      "fac_id": 2,
      "name_fa": "رستوران سنتی",
      "distance_km": 1.2,
      ...
    },
    ...
  ]
}
```

**Compare facilities**
```http
POST /api/facilities/compare/
Content-Type: application/json

{
  "facility_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "facilities": [
    {
      "fac_id": 1,
      "name_fa": "هتل A",
      "avg_rating": 4.5,
      "pricing": [...],
      "amenities": [...]
    },
    ...
  ],
  "comparison": {
    "ratings": {"max": 4.5, "min": 3.8, ...},
    "prices": {"max": 5000000, "min": 2000000, ...},
    "common_amenities": [...],
    "unique_amenities": {...}
  }
}
```

---

## Testing

### Run All Tests

```powershell
python manage.py test team4
```

### Run Specific Test Modules

```powershell
# Test models
python manage.py test team4.tests.test_models

# Test services  
python manage.py test team4.tests.test_services

# Test with verbose output
python manage.py test team4 --verbosity=2
```

### Test Coverage

```powershell
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run --source='team4' manage.py test team4
coverage report
coverage html

# View report at: htmlcov/index.html
```

---

## Development Workflow

### Adding New Facilities

#### Via Django Admin

1. Navigate to http://localhost:8000/admin/
2. Login with superuser credentials
3. Go to **Team4 > Facilities**
4. Click **Add Facility**
5. Fill in:
   - Names (Persian and English)
   - Category and City (from dropdowns)
   - Address
   - **Location**: Enter coordinates from Google Maps
     - Format: Latitude, Longitude
     - Example: 35.6892, 51.3890
   - Status and other fields
6. Add **Pricing** entries (bottom of form)
7. Add **Images** (bottom of form)
8. Select **Amenities** from multiselect
9. Save

#### Via API (Coming Soon)

POST endpoint for facility creation will be added in future iterations.

### Database Management

**Backup database:**
```powershell
mysqldump -u root -p team4_db > team4_backup.sql
```

**Restore database:**
```powershell
mysql -u root -p team4_db < team4_backup.sql
```

**Reset and reload:**
```powershell
# Drop and recreate database
python manage.py dbshell --database=team4
# In MySQL: DROP DATABASE team4_db; CREATE DATABASE team4_db;

# Reapply migrations
python manage.py migrate --database=team4

# Reload data
python manage.py load_provinces
python manage.py load_cities
```

---

## Troubleshooting

### Common Issues

#### 1. MySQL Connection Error

**Error:**
```
django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")
```

**Solution:**
- Verify MySQL service is running
- Check `.env` database URL
- Test connection: `mysql -u root -p`

#### 2. Table Doesn't Exist

**Error:**
```
django.db.utils.ProgrammingError: (1146, "Table 'team4_db.facilities_city' doesn't exist")
```

**Solution:**
```powershell
python manage.py migrate --database=team4
```

#### 3. Invalid POINT Value

**Error:**
```
MySQLdb.OperationalError: (1416, "Cannot get geometry object from data...")
```

**Solution:**
- Ensure coordinates are in correct format
- Check that `PointField.get_placeholder()` uses `ST_GeomFromText()`
- Verify data in format: `POINT(longitude latitude)`

#### 4. Port Already in Use

**Error:**
```
Error: That port is already in use.
```

**Solution:**
```powershell
# Use different port
python manage.py runserver 8001

# Or kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

#### 5. Migration Conflicts

**Error:**
```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

**Solution:**
```powershell
# Fake migrations to current state
python manage.py migrate --fake team4 --database=team4

# Or delete and recreate migrations
Remove-Item team4\migrations\0*.py
python manage.py makemigrations team4
python manage.py migrate --database=team4
```

---

## Performance Optimization

### Database Indexing

Key indexes already implemented:
- Province name (English)
- City + Province (composite)
- Facility + Category
- Facility + City
- Facility status

### Query Optimization

```python
# Use select_related for ForeignKey
City.objects.select_related('province').all()

# Use prefetch_related for Many-to-Many
Facility.objects.prefetch_related('amenities', 'images').all()

# Use only() to limit fields
Facility.objects.only('name_fa', 'avg_rating', 'location')
```

### Caching (Future Enhancement)

```python
from django.core.cache import cache

# Cache province list
provinces = cache.get('provinces_list')
if not provinces:
    provinces = list(Province.objects.all())
    cache.set('provinces_list', provinces, 3600)  # 1 hour
```

---

## Deployment Considerations

### Environment Variables

Create separate `.env` files for each environment:

**.env.development**
```env
DEBUG=True
TEAM4_DATABASE_URL=mysql://root:password@localhost:3306/team4_db
ALLOWED_HOSTS=localhost,127.0.0.1
```

**.env.production**
```env
DEBUG=False
TEAM4_DATABASE_URL=mysql://dbuser:secure_password@db.server.com:3306/team4_prod
ALLOWED_HOSTS=api.bugoff.com
SECRET_KEY=random_secure_key_here
```

### Database Security

```sql
-- Create dedicated database user
CREATE USER 'team4_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON team4_db.* TO 'team4_user'@'localhost';
FLUSH PRIVILEGES;
```

### HTTPS Configuration

Ensure all API calls use HTTPS in production.

### Rate Limiting

Implement rate limiting for API endpoints:

```python
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class FacilityViewSet(viewsets.ModelViewSet):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
```

---

## Project Structure

```
team4/
├── __init__.py
├── admin.py              # Django admin configuration
├── models.py             # Database models (8 models)
├── serializers.py        # DRF serializers
├── views.py              # API ViewSets
├── urls.py               # URL routing
├── fields.py             # Custom PointField
├── services/
│   ├── __init__.py
│   └── facility_service.py  # Business logic
├── management/
│   └── commands/
│       ├── load_provinces.py
│       ├── load_cities.py
│       ├── show_stats.py
│       └── create_city_table.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   └── test_services.py
├── fixtures/
│   ├── provinces.json    # 31 provinces
│   └── cities.json       # 1112 cities
├── docs/
│   ├── CHECKLIST.md
│   ├── SETUP_GUIDE.md    # This file
│   └── SUMMARY.md
└── templates/
    └── team4/
        └── index.html
```

---

## Next Steps

### Immediate Tasks
1. ✅ Add at least 10 sample facilities via Django Admin
2. ✅ Test all API endpoints thoroughly
3. ✅ Verify geolocation calculations
4. ⏳ Document any custom business rules

### Integration with Other Teams
- **Team 2**: Provide API documentation for map integration
- **Team 3**: Coordinate on additional API endpoints
- **Frontend**: Provide API base URL and authentication details

### Future Enhancements
- Implement JWT authentication
- Add facility creation/update APIs
- Implement caching layer
- Add real-time updates via WebSockets
- Integrate with external map services (Neshan, Google Maps)

---

## Resources

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [MySQL Spatial Extensions](https://dev.mysql.com/doc/refman/8.0/en/spatial-extensions.html)

### Tools
- [MySQL Workbench](https://www.mysql.com/products/workbench/)
- [Postman](https://www.postman.com/) - API testing
- [DB Browser](https://dbeaver.io/) - Database management

### Project Files
- [README.md](../README.md) - Project overview
- [CHECKLIST.md](CHECKLIST.md) - Deployment checklist
- [SUMMARY.md](SUMMARY.md) - Feature summary

---

## Support

For questions or issues:
1. Check this guide and other documentation
2. Review Django/DRF documentation
3. Contact team lead
4. Create issue in project repository

---

**Document Version**: 1.0.0  
**Last Updated**: February 8, 2026  
**Author**: Team 4 Backend Developer  
**Status**: Production Ready ✅
