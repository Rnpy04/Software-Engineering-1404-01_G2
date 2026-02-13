"""
Facility Service Client - Communicates with Team 4's Facility Service (REST)
"""
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class FacilityClient:
    """
    Client for communicating with Facility Service via REST API (Team 4)
    Fallback to mocks if configured or connection fails.
    """

    def __init__(self, base_url: str = 'http://localhost:8000/team4/api', use_mocks: bool = False):
        self.base_url = base_url.rstrip('/')
        self.use_mocks = use_mocks
        if self.use_mocks:
            logger.info("FacilityClient initializes in MOCK mode")
        else:
            logger.info(f"FacilityClient initialized with base_url: {self.base_url}")

    def search_places(
            self,
            province: str,
            city: Optional[str] = None,
            categories: Optional[List[str]] = None,
            budget_level: Optional[str] = None,
            limit: int = 20
    ) -> List[Dict]:
        """
        Search for places based on criteria
        Protocol: POST /facilities/search/
        """
        if self.use_mocks:
            return self._get_mock_places(province, city, categories, limit)

        try:
            # Prepare payload for Team 4 API
            payload = {}
            if province:
                payload['province'] = province
            if city:
                payload['city'] = city
            if categories:
                # API accepts single category string, we might need to loop or pick first?
                # The doc says "category": "string". If we have multiple, we might need multiple calls or just send one.
                # For now, let's send the first one if available.
                payload['category'] = categories[0]

            if budget_level:
                # Map our budget levels to theirs if needed
                # Ours: ECONOMY, MEDIUM, LUXURY
                # Theirs: free, budget, moderate, expensive, luxury
                budget_map = {
                    'ECONOMY': 'budget',
                    'MEDIUM': 'moderate',
                    'LUXURY': 'luxury',
                    'UNLIMITED': 'luxury'
                }
                payload['price_tier'] = budget_map.get(budget_level, 'moderate')

            # Pagination
            params = {'page': 1, 'page_size': limit}

            response = requests.post(
                f"{self.base_url}/facilities/search/",
                json=payload,
                params=params,
                timeout=5
            )
            response.raise_for_status()
            data = response.json()

            # Map response to our internal format
            results = []
            for item in data.get('results', []):
                results.append(self._map_place_to_internal(item))

            return results

        except Exception as e:
            logger.error(f"Error in search_places: {e}. Falling back to mocks.")
            return self._get_mock_places(province, city, categories, limit)

    def get_place_by_id(self, place_id: str) -> Optional[Dict]:
        """Get detailed information about a specific place"""
        if self.use_mocks:
            return self._get_mock_place(place_id)

        try:
            # Assuming place_id is an integer for Team 4, but we use strings mostly.
            # If our internal IDs are "place_001", we might need to handle that.
            # Team 4 IDs are integers.
            clean_id = place_id
            if str(place_id).startswith('place_'):
                 # It's a mock ID, fallback to mock
                 return self._get_mock_place(place_id)

            response = requests.get(
                f"{self.base_url}/facilities/{clean_id}/",
                timeout=5
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self._map_place_to_internal(response.json(), detailed=True)

        except Exception as e:
            logger.error(f"Error in get_place_by_id: {e}")
            return self._get_mock_place(place_id)

    def check_availability(
            self,
            place_id: str,
            date: str,
            start_time: str,
            end_time: str
    ) -> Dict:
        """Check if a place is available (Mock only for now)"""
        return {'is_available': True, 'reason': '', 'suggested_times': []}

    def _map_place_to_internal(self, item: Dict, detailed: bool = False) -> Dict:
        """Map Team 4 API response to our internal dictionary format"""
        # Team 4: fac_id, name_fa, category (string or obj), ...
        
        # Handle Category: could be string or object
        category = "OTHER"
        cat_raw = item.get('category')
        if isinstance(cat_raw, dict):
             cat_name = cat_raw.get('name_en', '').upper()
        else:
             cat_name = str(cat_raw).upper()
        
        # Simple mapping heuristics
        if 'HOTEL' in cat_name or 'STAY' in cat_name: category = 'STAY'
        elif 'RESTAURANT' in cat_name or 'DINING' in cat_name or 'CAFE' in cat_name: category = 'DINING'
        elif 'PARK' in cat_name or 'NATURE' in cat_name: category = 'NATURAL'
        elif 'MUSEUM' in cat_name or 'HISTORICAL' in cat_name: category = 'HISTORICAL'
        elif 'MOSQUE' in cat_name or 'RELIGIOUS' in cat_name: category = 'RELIGIOUS'
        
        # Lat/Lng
        lat, lng = 0.0, 0.0
        loc = item.get('location')
        if isinstance(loc, dict) and loc.get('coordinates'):
            # GeoJSON is [lng, lat]
            lng, lat = loc['coordinates']

        # Price Tier
        price_tier_map = {
             'free': 'FREE', 'budget': 'BUDGET', 'moderate': 'MODERATE', 
             'expensive': 'EXPENSIVE', 'luxury': 'LUXURY'
        }
        price_tier = price_tier_map.get(item.get('price_tier'), 'MODERATE')
        
        # Entry Fee
        entry_fee = 0
        price_info = item.get('price_from')
        if isinstance(price_info, dict):
             entry_fee = price_info.get('amount', 0)

        # Images
        images = []
        if item.get('primary_image'):
             images.append(item['primary_image'])
        if detailed and item.get('images'):
             for img in item.get('images', []):
                  if isinstance(img, dict) and img.get('image_url'):
                       images.append(img['image_url'])

        return {
            'id': str(item.get('fac_id')),
            'title': item.get('name_fa'),
            'category': category,
            'address': item.get('address') or f"{item.get('city')} - {item.get('province')}",
            'lat': lat,
            'lng': lng,
            'entry_fee': entry_fee,
            'price_tier': price_tier,
            'description': item.get('description_fa') or item.get('name_en'),
            'images': images,
            'opening_hours': {'24/7': item.get('is_24_hour', False)},
            'rating': float(item.get('avg_rating') or 0),
            'review_count': item.get('review_count', 0)
        }

    def _get_mock_places(
            self,
            province: str,
            city: Optional[str],
            categories: Optional[List[str]],
            limit: int
    ) -> List[Dict]:
        """Mock data for development - replace with actual gRPC calls"""
        mock_places = [
            {
                'id': 'place_001',
                'title': 'میدان نقش جهان',
                'category': 'HISTORICAL',
                'address': 'اصفهان، میدان نقش جهان',
                'lat': 32.6546,
                'lng': 51.6777,
                'entry_fee': 200000,
                'price_tier': 'BUDGET',
                'description': 'یکی از بزرگترین میدان‌های جهان',
                'images': [],
                'opening_hours': {'daily': '08:00-22:00'},
                'rating': 4.8,
                'review_count': 1250
            },
            {
                'id': 'place_002',
                'title': 'مسجد شیخ لطف الله',
                'category': 'RELIGIOUS',
                'address': 'اصفهان، میدان نقش جهان',
                'lat': 32.6565,
                'lng': 51.6785,
                'entry_fee': 500000,
                'price_tier': 'MODERATE',
                'description': 'شاهکار معماری دوران صفوی',
                'images': [],
                'opening_hours': {'daily': '09:00-17:00'},
                'rating': 4.9,
                'review_count': 980
            },
            {
                'id': 'place_003',
                'title': 'رستوران سنتی شاهرزاد',
                'category': 'DINING',
                'address': 'اصفهان، خیابان چهارباغ',
                'lat': 32.6543,
                'lng': 51.6724,
                'entry_fee': 0,
                'price_tier': 'MODERATE',
                'description': 'رستوران سنتی با غذاهای محلی',
                'images': [],
                'opening_hours': {'daily': '12:00-23:00'},
                'rating': 4.5,
                'review_count': 450
            },
            {
                'id': 'hotel_001',
                'title': 'هتل عباسی',
                'category': 'STAY',
                'address': 'اصفهان، خیابان چهارباغ',
                'lat': 32.6565,
                'lng': 51.6750,
                'entry_fee': 5000000,
                'price_tier': 'LUXURY',
                'description': 'هتل تاریخی 5 ستاره',
                'images': [],
                'opening_hours': {'24/7': True},
                'rating': 4.7,
                'review_count': 820
            },
            {
                'id': 'place_004',
                'title': 'پل سی‌وسه‌پل',
                'category': 'HISTORICAL',
                'address': 'اصفهان، زاینده رود',
                'lat': 32.6479,
                'lng': 51.6698,
                'entry_fee': 0,
                'price_tier': 'FREE',
                'description': 'پل تاریخی دوران صفوی',
                'images': [],
                'opening_hours': {'24/7': True},
                'rating': 4.8,
                'review_count': 1520
            },
            {
                'id': 'place_005',
                'title': 'باغ چهلستون',
                'category': 'CULTURAL',
                'address': 'اصفهان، خیابان استانداری',
                'lat': 32.6612,
                'lng': 51.6697,
                'entry_fee': 150000,
                'price_tier': 'BUDGET',
                'description': 'کاخ موزه با باغ زیبا',
                'images': [],
                'opening_hours': {'daily': '08:30-18:00'},
                'rating': 4.6,
                'review_count': 750
            },
            {
                'id': 'restaurant_001',
                'title': 'رستوران هتل عباسی',
                'category': 'DINING',
                'address': 'اصفهان، هتل عباسی',
                'lat': 32.6570,
                'lng': 51.6755,
                'entry_fee': 0,
                'price_tier': 'EXPENSIVE',
                'description': 'رستوران لوکس با غذاهای بین‌المللی',
                'images': [],
                'opening_hours': {'daily': '07:00-23:00'},
                'rating': 4.6,
                'review_count': 320
            },
            {
                'id': 'restaurant_002',
                'title': 'کافه آرت اصفهان',
                'category': 'DINING',
                'address': 'اصفهان، خیابان چهارباغ',
                'lat': 32.6540,
                'lng': 51.6730,
                'entry_fee': 0,
                'price_tier': 'BUDGET',
                'description': 'کافه هنری با فضای دنج',
                'images': [],
                'opening_hours': {'daily': '10:00-23:00'},
                'rating': 4.3,
                'review_count': 280
            },
        ]

        # Filter by province/city
        filtered = [p for p in mock_places if province in p['address']]
        if city:
            filtered = [p for p in filtered if city in p['address']]

        # Filter by categories
        if categories:
            filtered = [p for p in filtered if p['category'] in categories]

        return filtered[:limit]

    def _get_mock_place(self, place_id: str) -> Optional[Dict]:
        """Get mock place by ID"""
        places = self._get_mock_places('', None, None, 100)
        for place in places:
            if place['id'] == place_id:
                return place
        return None

    def close(self):
        """Close gRPC connection"""
        if self.channel:
            self.channel.close()
            logger.info("Closed connection to Facility Service")
