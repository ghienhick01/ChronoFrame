from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Album, AlbumCollaborator


class AlbumOwnerMixin(LoginRequiredMixin):
    """Only the album owner can perform this action."""

    def get_album(self):
        return get_object_or_404(Album, pk=self.kwargs.get('album_pk') or self.kwargs.get('pk'))

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        album = self.get_album()
        if album.owner != request.user and not request.user.is_staff:
            raise PermissionDenied
        return response


class AlbumAccessMixin(LoginRequiredMixin):
    """Allow owner, collaborators, or staff to access."""

    def get_album(self):
        return get_object_or_404(Album, pk=self.kwargs.get('album_pk') or self.kwargs.get('pk'))

    def get_user_role(self, album):
        if self.request.user == album.owner or self.request.user.is_staff:
            return 'owner'
        try:
            collab = AlbumCollaborator.objects.get(album=album, user=self.request.user)
            return collab.role
        except AlbumCollaborator.DoesNotExist:
            return None

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        album = self.get_album()
        if album.visibility == 'private':
            role = self.get_user_role(album)
            if role is None:
                raise PermissionDenied
        return response


class AlbumContributorMixin(AlbumAccessMixin):
    """Allow owner or contributors to upload photos."""

    def dispatch(self, request, *args, **kwargs):
        response = LoginRequiredMixin.dispatch(self, request, *args, **kwargs)
        album = self.get_album()
        role = self.get_user_role(album)
        if role not in ('owner', 'admin', 'contributor'):
            raise PermissionDenied
        return response
