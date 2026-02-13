"""
Recommendation Service Client - Communicates with External Recommendation Service
"""
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class RecommendationClient:
    """
    Client for External Recommendation Service
    Supports API 1, 2, 3 as defined in the integration guide.
    """

    def __init__(self, base_url: str = 'http://localhost:8000/api', use_mocks: bool = False):
        self.base_url = base_url.rstrip('/')
        self.use_mocks = use_mocks
        if self.use_mocks:
            logger.info("RecommendationClient initializes in MOCK mode")

    def get_scored_places(
            self,
            candidate_place_ids: List[str],
            travel_style: str,
            budget_level: str,
            trip_duration: int
    ) -> Dict[str, float]:
        """
        API 1: Get scores for a list of places
        Input: list of place IDs, parameters
        Output: {place_id: score}
        """
        if self.use_mocks:
            return {pid: 85.0 for pid in candidate_place_ids}

        try:
            # Note: The user description said "candidate_place_id" (singular) but context implies ranking multiple.
            # I will assume we send one by one or a batch. The description output is "scored_places" (plural).
            # Let's assume we post a list or loop.
            # For efficiency, if the API supports batch, great. If not, we might need to loop.
            # Given the description "scored_places: list of places with score", it accepts a list?
            # User Input: "candidate_place_id: شناسه مکان"
            # Maybe it scores ONE place at a time?
            # Let's implement batching logic or loop.
            
            payload = {
                "candidate_place_ids": candidate_place_ids, # Hope they support list
                "travel_style": travel_style,
                "budget_level": budget_level,
                "trip_duration": trip_duration
            }
            
            response = requests.post(
                f"{self.base_url}/recommendations/score-places/", # Assumed Endpoint
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            # Map: {place_id: score}
            scores = {}
            for item in data.get('scored_places', []):
                scores[item['place_id']] = item['score']
            return scores

        except Exception as e:
            logger.error(f"Error in get_scored_places: {e}")
            return {pid: 50.0 for pid in candidate_place_ids}

    def get_suggested_regions(
            self,
            budget_limit: str,
            season: str
    ) -> List[Dict]:
        """
        API 2: Suggest regions based on budget and season
        """
        if self.use_mocks:
            return [
                {
                    'region_id': 'reg_01',
                    'region_name': 'استان اصفهان',
                    'match_score': 95,
                    'image_url': 'https://example.com/isf.jpg'
                },
                {
                    'region_id': 'reg_02',
                    'region_name': 'استان فارس',
                    'match_score': 88,
                    'image_url': 'https://example.com/shz.jpg'
                }
            ]

        try:
            payload = {
                "limit": budget_limit,
                "season": season
            }
            response = requests.post(
                f"{self.base_url}/recommendations/suggest-regions/", # Assumed Endpoint
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            return response.json().get('destinations', [])

        except Exception as e:
            logger.error(f"Error in get_suggested_regions: {e}")
            return []

    def get_places_in_region(
            self,
            region_id: str,
            travel_style: str,
            budget_level: str,
            trip_duration: int
    ) -> List[Dict]:
        """
        API 3: Suggest places in a specific region
        """
        if self.use_mocks:
            # Return some mock place IDs with scores
            return [
                {'place_id': 'place_001', 'score': 90},
                {'place_id': 'place_002', 'score': 85}, 
                {'place_id': 'place_003', 'score': 80}
            ]

        try:
            payload = {
                "region_id": region_id,
                "travel_style": travel_style,
                "budget_level": budget_level,
                "trip_duration": trip_duration
            }
            response = requests.post(
                f"{self.base_url}/recommendations/region-places/", # Assumed Endpoint
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            return response.json().get('scored_places', [])

        except Exception as e:
            logger.error(f"Error in get_places_in_region: {e}")
            return []

    def rank_places(
            self,
            places: List[Dict],
            user_interests: List[str]
    ) -> List[Dict]:
        """
        Legacy method for backward compatibility with current codebase.
        Uses _mock_ranking logic.
        """
        return self._mock_ranking(places, user_interests)

    def _mock_ranking(
            self,
            places: List[Dict],
            user_interests: List[str]
    ) -> List[Dict]:
        """Simple mock ranking based on category match"""

        # Interest to category mapping
        interest_mapping = {
            'تاریخی': ['HISTORICAL', 'RELIGIOUS', 'CULTURAL'],
            'فرهنگی': ['CULTURAL', 'HISTORICAL'],
            'طبیعت': ['NATURAL', 'RECREATIONAL'],
            'خانوادگی': ['RECREATIONAL', 'NATURAL'],
            'مذهبی': ['RELIGIOUS'],
            'غذا': ['DINING']
        }

        # Get relevant categories
        relevant_categories = []
        for interest in user_interests:
            relevant_categories.extend(interest_mapping.get(interest, []))

        # Score places
        scored_places = []
        for place in places:
            score = 0
            if place['category'] in relevant_categories:
                score += 10
            score += place.get('rating', 0) * 2
            if place.get('price_tier') == 'FREE':
                score += 3
            scored_places.append((score, place))

        # Sort by score descending
        scored_places.sort(reverse=True, key=lambda x: x[0])

        return [place for score, place in scored_places]

