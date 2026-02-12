from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from typing import Optional

from business.services import (
    TripService, TripDayService, TripItemService,
    DependencyService, ShareService, VotingService,
    ReviewService, MediaService
)
from .serializers import (
    TripListSerializer, TripDetailSerializer, TripCreateUpdateSerializer,
    TripDaySerializer, TripItemSerializer, ItemDependencySerializer,
    ShareLinkSerializer, VoteSerializer, TripReviewSerializer,
    UserMediaSerializer
)


def test(request):
    """Test endpoint for development"""
    trips = TripService.get_all_trips()
    return JsonResponse({
        "status": "ok",
        "count": len(trips),
        "trips": [
            {"id": str(t.trip_id), "title": t.title, "province": t.province}
            for t in trips
        ]
    })


def ok(request):
    """Health check endpoint"""
    return JsonResponse({
        "response": "ok and fine"
    })


class TripViewSet(viewsets.ViewSet):
    """API endpoints for Trip management"""
    
    def list(self, request):
        """GET /api/trips/ - List all trips"""
        user_id = request.query_params.get('user_id')
        status_filter = request.query_params.get('status')
        
        trips = TripService.get_all_trips(
            user_id=int(user_id) if user_id else None,
            status=status_filter
        )
        
        serializer = TripListSerializer(trips, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """GET /api/trips/{id}/ - Get trip details"""
        trip = TripService.get_trip_detail(int(pk))
        
        if not trip:
            return Response(
                {"error": "Trip not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TripDetailSerializer(trip)
        return Response(serializer.data)
    
    def create(self, request):
        """POST /api/trips/ - Create a new trip"""
        serializer = TripCreateUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_id = request.data.get('user_id')
            trip = TripService.create_trip(
                user_id=int(user_id) if user_id else None,
                data=serializer.validated_data
            )
            
            return Response(
                TripDetailSerializer(trip).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, pk=None):
        """PUT /api/trips/{id}/ - Update a trip"""
        serializer = TripCreateUpdateSerializer(data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        trip = TripService.update_trip(int(pk), serializer.validated_data)
        
        if not trip:
            return Response(
                {"error": "Trip not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(TripDetailSerializer(trip).data)
    
    def destroy(self, request, pk=None):
        """DELETE /api/trips/{id}/ - Delete a trip"""
        if TripService.delete_trip(int(pk)):
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(
            {"error": "Trip not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=True, methods=['post'])
    def copy(self, request, pk=None):
        """POST /api/trips/{id}/copy/ - Copy an existing trip"""
        user_id = request.data.get('user_id')
        
        trip = TripService.copy_trip(
            int(pk),
            user_id=int(user_id) if user_id else None
        )
        
        if not trip:
            return Response(
                {"error": "Original trip not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            TripDetailSerializer(trip).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        """POST /api/trips/{id}/finalize/ - Finalize a trip"""
        trip = TripService.finalize_trip(int(pk))
        
        if not trip:
            return Response(
                {"error": "Trip not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(TripDetailSerializer(trip).data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """GET /api/trips/search/?q=query - Search trips"""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {"error": "Search query required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        trips = TripService.search_trips(query)
        serializer = TripListSerializer(trips, many=True)
        return Response(serializer.data)


class TripDayViewSet(viewsets.ViewSet):
    """API endpoints for TripDay management"""
    
    def list(self, request):
        """GET /api/trip-days/?trip_id=X - List days for a trip"""
        trip_id = request.query_params.get('trip_id')
        
        if not trip_id:
            return Response(
                {"error": "trip_id parameter required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        days = TripDayService.get_days_for_trip(int(trip_id))
        serializer = TripDaySerializer(days, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """POST /api/trip-days/ - Create a new day"""
        serializer = TripDaySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        trip_id = request.data.get('trip_id')
        if not trip_id:
            return Response(
                {"error": "trip_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        day = TripDayService.create_day(int(trip_id), serializer.validated_data)
        return Response(
            TripDaySerializer(day).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, pk=None):
        """PUT /api/trip-days/{id}/ - Update a day"""
        serializer = TripDaySerializer(data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        day = TripDayService.update_day(int(pk), serializer.validated_data)
        
        if not day:
            return Response(
                {"error": "Day not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(TripDaySerializer(day).data)
    
    def destroy(self, request, pk=None):
        """DELETE /api/trip-days/{id}/ - Delete a day"""
        if TripDayService.delete_day(int(pk)):
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(
            {"error": "Day not found"},
            status=status.HTTP_404_NOT_FOUND
        )


class TripItemViewSet(viewsets.ViewSet):
    """API endpoints for TripItem management"""
    
    def list(self, request):
        """GET /api/trip-items/?day_id=X - List items for a day"""
        day_id = request.query_params.get('day_id')
        
        if not day_id:
            return Response(
                {"error": "day_id parameter required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        items = TripItemService.get_items_for_day(int(day_id))
        serializer = TripItemSerializer(items, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """POST /api/trip-items/ - Create a new item"""
        serializer = TripItemSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        day_id = request.data.get('day_id')
        if not day_id:
            return Response(
                {"error": "day_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = TripItemService.create_item(int(day_id), serializer.validated_data)
            return Response(
                TripItemSerializer(item).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, pk=None):
        """PUT /api/trip-items/{id}/ - Update an item"""
        serializer = TripItemSerializer(data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = TripItemService.update_item(int(pk), serializer.validated_data)
            
            if not item:
                return Response(
                    {"error": "Item not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(TripItemSerializer(item).data)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, pk=None):
        """DELETE /api/trip-items/{id}/ - Delete an item"""
        if TripItemService.delete_item(int(pk)):
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(
            {"error": "Item not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """POST /api/trip-items/{id}/lock/ - Lock an item"""
        item = TripItemService.lock_item(int(pk))
        
        if not item:
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(TripItemSerializer(item).data)
    
    @action(detail=True, methods=['post'])
    def unlock(self, request, pk=None):
        """POST /api/trip-items/{id}/unlock/ - Unlock an item"""
        item = TripItemService.unlock_item(int(pk))
        
        if not item:
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(TripItemSerializer(item).data)
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """POST /api/trip-items/reorder/ - Reorder items in a day"""
        day_id = request.data.get('day_id')
        item_order = request.data.get('item_order', [])
        
        if not day_id or not item_order:
            return Response(
                {"error": "day_id and item_order required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        TripItemService.reorder_items(int(day_id), item_order)
        return Response({"success": True})
