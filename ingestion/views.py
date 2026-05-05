from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ingestion.services.ingestion import IngestionService, IngestionType


def health(_request):
    return JsonResponse({"status": "ok", "framework": "django"})


def _upload(request, ingestion_type: IngestionType):
    if request.method != "POST":
        return JsonResponse({"detail": "Only POST is allowed."}, status=405)

    uploaded_file = request.FILES.get("file")
    if uploaded_file is None:
        return JsonResponse({"detail": "file is required."}, status=400)
    if not uploaded_file.name.lower().endswith(".csv"):
        return JsonResponse({"detail": "Only CSV uploads are supported."}, status=400)

    summary = IngestionService().ingest(uploaded_file, ingestion_type)
    return JsonResponse(summary)


@csrf_exempt
def upload_stores(request):
    return _upload(request, IngestionType.STORES)


@csrf_exempt
def upload_users(request):
    return _upload(request, IngestionType.USERS)


@csrf_exempt
def upload_mapping(request):
    return _upload(request, IngestionType.MAPPINGS)
