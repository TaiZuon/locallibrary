"""catalog/urls.py"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("books/", views.BookListView.as_view(), name="books"),
    path("books/<int:pk>/", views.BookDetailView.as_view(), name="book-detail"),
]

urlpatterns += [
    path(
        "mybooks/",
        views.LoanedBooksByUserListView.as_view(),
        name="my-borrowed",
    ),
    path(
        "books/<uuid:pk>/return/",
        views.MarkBookAsReturnedView.as_view(),
        name="mark-returned",
    ),
]

urlpatterns += [
    path(
        "books/<uuid:pk>/renew/",
        views.renew_book_librarian,
        name="renew-book-librarian",
    ),
]

urlpatterns += [
    path("authors/", views.AuthorListView.as_view(), name="authors"),
    path(
        "authors/<int:pk>/",
        views.AuthorDetailView.as_view(),
        name="author-detail",
    ),
    path(
        "authors/create/",
        views.AuthorCreateView.as_view(),
        name="author-create",
    ),
    path(
        "authors/<int:pk>/update/",
        views.AuthorUpdateView.as_view(),
        name="author-update",
    ),
    path(
        "authors/<int:pk>/delete/",
        views.AuthorDeleteView.as_view(),
        name="author-delete",
    ),
]
