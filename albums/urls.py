from django.urls import path
from . import views

app_name = 'albums'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('my-albums/', views.MyAlbumsView.as_view(), name='my-albums'),
    path('albums/create/', views.AlbumCreateView.as_view(), name='album-create'),
    path('albums/<int:pk>/', views.AlbumDetailView.as_view(), name='album-detail'),
    path('albums/<int:pk>/edit/', views.AlbumUpdateView.as_view(), name='album-edit'),
    path('albums/<int:pk>/delete/', views.AlbumDeleteView.as_view(), name='album-delete'),
    path('albums/<int:album_pk>/photos/upload/', views.PhotoUploadView.as_view(), name='photo-upload'),
    path('albums/<int:album_pk>/photos/<int:pk>/', views.PhotoDetailView.as_view(), name='photo-detail'),
    path('albums/<int:album_pk>/photos/<int:pk>/edit/', views.PhotoUpdateView.as_view(), name='photo-edit'),
    path('albums/<int:album_pk>/photos/<int:pk>/delete/', views.PhotoDeleteView.as_view(), name='photo-delete'),
    path('albums/<int:album_pk>/collaborators/add/', views.CollaboratorAddView.as_view(), name='collaborator-add'),
    path('albums/<int:album_pk>/collaborators/<int:user_pk>/remove/', views.CollaboratorRemoveView.as_view(), name='collaborator-remove'),
]
