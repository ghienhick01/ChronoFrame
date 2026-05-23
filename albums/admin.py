from django.contrib import admin
from .models import Album, Photo, AlbumCollaborator


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'visibility', 'photo_count', 'created_at']
    list_filter = ['visibility', 'created_at']
    search_fields = ['title', 'owner__username']
    raw_id_fields = ['owner']


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'album', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['title', 'album__title', 'uploaded_by__username']
    raw_id_fields = ['album', 'uploaded_by']


@admin.register(AlbumCollaborator)
class AlbumCollaboratorAdmin(admin.ModelAdmin):
    list_display = ['user', 'album', 'role', 'added_at']
    list_filter = ['role']
