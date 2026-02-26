from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


@csrf_exempt
def stripe_webhook(request):
    return HttpResponse(status=200)
