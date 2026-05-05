from django.urls import path

from ingestion import views


urlpatterns = [
    path("health", views.health, name="health"),
    path("upload/stores", views.upload_stores, name="upload_stores"),
    path("upload/users", views.upload_users, name="upload_users"),
    path("upload/mapping", views.upload_mapping, name="upload_mapping"),
]
