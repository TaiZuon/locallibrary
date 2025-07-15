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
