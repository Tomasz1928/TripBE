from django.http import JsonResponse


def keep_alive(request):
    return JsonResponse({"status": "ok"})