from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from .models import Album, Photo, AlbumCollaborator
from .forms import AlbumForm, PhotoForm, CollaboratorForm
from .mixins import AlbumOwnerMixin, AlbumAccessMixin, AlbumContributorMixin


class HomeView(ListView):
    model = Album
    template_name = 'albums/home.html'
    context_object_name = 'albums'
    paginate_by = 12

    def get_queryset(self):
        qs = Album.objects.filter(visibility='public')
        if self.request.user.is_authenticated:
            user_albums = Album.objects.filter(owner=self.request.user)
            collab_albums = Album.objects.filter(collaborators__user=self.request.user)
            qs = (qs | user_albums | collab_albums).distinct()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_query'] = self.request.GET.get('q', '')
        return ctx


class MyAlbumsView(LoginRequiredMixin, ListView):
    model = Album
    template_name = 'albums/my_albums.html'
    context_object_name = 'albums'
    paginate_by = 12

    def get_queryset(self):
        return Album.objects.filter(owner=self.request.user).order_by('-created_at')


class AlbumDetailView(AlbumAccessMixin, DetailView):
    model = Album
    template_name = 'albums/album_detail.html'
    context_object_name = 'album'

    def get_album(self):
        return self.get_object()

    def dispatch(self, request, *args, **kwargs):
        album = get_object_or_404(Album, pk=kwargs['pk'])
        if album.visibility == 'public':
            return View.dispatch(self, request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        album = self.object
        ctx['photos'] = album.photos.all()
        ctx['is_owner'] = self.request.user == album.owner
        ctx['is_staff'] = self.request.user.is_staff
        if self.request.user.is_authenticated:
            try:
                collab = AlbumCollaborator.objects.get(album=album, user=self.request.user)
                ctx['user_role'] = collab.role
            except AlbumCollaborator.DoesNotExist:
                ctx['user_role'] = 'owner' if ctx['is_owner'] else None
        ctx['collaborators'] = album.collaborators.select_related('user').all()
        ctx['photo_form'] = PhotoForm()
        return ctx


class AlbumCreateView(LoginRequiredMixin, CreateView):
    model = Album
    form_class = AlbumForm
    template_name = 'albums/album_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Album created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Create'
        return ctx


class AlbumUpdateView(AlbumOwnerMixin, UpdateView):
    model = Album
    form_class = AlbumForm
    template_name = 'albums/album_form.html'

    def get_album(self):
        return self.get_object()

    def form_valid(self, form):
        messages.success(self.request, 'Album updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Edit'
        return ctx


class AlbumDeleteView(AlbumOwnerMixin, DeleteView):
    model = Album
    template_name = 'albums/album_confirm_delete.html'
    success_url = reverse_lazy('albums:my-albums')

    def get_album(self):
        return self.get_object()

    def form_valid(self, form):
        messages.success(self.request, 'Album deleted.')
        return super().form_valid(form)


class PhotoDetailView(DetailView):
    model = Photo
    template_name = 'albums/photo_detail.html'
    context_object_name = 'photo'

    def get_object(self):
        return get_object_or_404(Photo, pk=self.kwargs['pk'], album_id=self.kwargs['album_pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        photo = self.object
        photos = list(photo.album.photos.values_list('pk', flat=True))
        idx = photos.index(photo.pk)
        ctx['prev_photo'] = Photo.objects.get(pk=photos[idx - 1]) if idx > 0 else None
        ctx['next_photo'] = Photo.objects.get(pk=photos[idx + 1]) if idx < len(photos) - 1 else None
        ctx['is_owner'] = self.request.user == photo.album.owner
        ctx['can_delete'] = ctx['is_owner'] or self.request.user == photo.uploaded_by
        return ctx


class PhotoUploadView(AlbumContributorMixin, View):
    def get_album(self):
        return get_object_or_404(Album, pk=self.kwargs['album_pk'])

    def post(self, request, album_pk):
        album = get_object_or_404(Album, pk=album_pk)
        images = request.FILES.getlist('images')
        if not images:
            messages.error(request, 'Please select at least one image.')
            return redirect('albums:album-detail', pk=album_pk)
        count = 0
        for image in images:
            title = request.POST.get('title', '')
            caption = request.POST.get('caption', '')
            Photo.objects.create(
                album=album,
                image=image,
                title=title,
                caption=caption,
                uploaded_by=request.user
            )
            count += 1
        messages.success(request, f'{count} photo(s) uploaded successfully!')
        return redirect('albums:album-detail', pk=album_pk)


class PhotoUpdateView(LoginRequiredMixin, UpdateView):
    model = Photo
    form_class = PhotoForm
    template_name = 'albums/photo_form.html'

    def get_object(self):
        return get_object_or_404(Photo, pk=self.kwargs['pk'], album_id=self.kwargs['album_pk'])

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        photo = self.get_object()
        if photo.album.owner != request.user and photo.uploaded_by != request.user and not request.user.is_staff:
            raise PermissionDenied
        return response

    def get_success_url(self):
        return reverse('albums:photo-detail', kwargs={'album_pk': self.object.album.pk, 'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Photo updated!')
        return super().form_valid(form)


class PhotoDeleteView(LoginRequiredMixin, DeleteView):
    model = Photo
    template_name = 'albums/photo_confirm_delete.html'

    def get_object(self):
        return get_object_or_404(Photo, pk=self.kwargs['pk'], album_id=self.kwargs['album_pk'])

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        photo = self.get_object()
        if photo.album.owner != request.user and photo.uploaded_by != request.user and not request.user.is_staff:
            raise PermissionDenied
        return response

    def get_success_url(self):
        return reverse('albums:album-detail', kwargs={'pk': self.object.album.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Photo deleted.')
        return super().form_valid(form)


class CollaboratorAddView(AlbumOwnerMixin, View):
    def get_album(self):
        return get_object_or_404(Album, pk=self.kwargs['album_pk'])

    def post(self, request, album_pk):
        album = get_object_or_404(Album, pk=album_pk)
        form = CollaboratorForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['username']
            role = form.cleaned_data['role']
            if user == album.owner:
                messages.error(request, 'Cannot add the owner as a collaborator.')
            else:
                obj, created = AlbumCollaborator.objects.update_or_create(
                    album=album, user=user,
                    defaults={'role': role}
                )
                action = 'added' if created else 'updated'
                messages.success(request, f'{user.username} {action} as {role}.')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
        return redirect('albums:album-detail', pk=album_pk)


class CollaboratorRemoveView(AlbumOwnerMixin, View):
    def get_album(self):
        return get_object_or_404(Album, pk=self.kwargs['album_pk'])

    def post(self, request, album_pk, user_pk):
        album = get_object_or_404(Album, pk=album_pk)
        AlbumCollaborator.objects.filter(album=album, user_id=user_pk).delete()
        messages.success(request, 'Collaborator removed.')
        return redirect('albums:album-detail', pk=album_pk)
