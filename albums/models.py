from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Album(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='albums')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    cover_image = models.ImageField(upload_to='album_covers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('albums:album-detail', kwargs={'pk': self.pk})

    @property
    def photo_count(self):
        return self.photos.count()

    @property
    def cover(self):
        if self.cover_image:
            return self.cover_image
        first_photo = self.photos.first()
        if first_photo:
            return first_photo.image
        return None


class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='photos/')
    title = models.CharField(max_length=200, blank=True)
    caption = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='photos')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title or f"Photo in {self.album.title}"

    def get_absolute_url(self):
        return reverse('albums:photo-detail', kwargs={'album_pk': self.album.pk, 'pk': self.pk})


class AlbumCollaborator(models.Model):
    ROLE_CHOICES = [
        ('viewer', 'Viewer'),
        ('contributor', 'Contributor'),
        ('admin', 'Admin'),
    ]

    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='collaborators')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collaborations')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['album', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.album.title} ({self.role})"
