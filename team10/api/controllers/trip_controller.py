from django.http import JsonResponse

def ping(request):
    return JsonResponse({"team": 10, "service": "trip-plan", "status": "ok"})
