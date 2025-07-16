"""catalog/views.py"""

import datetime
from urllib import request

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
    LoginRequiredMixin,
)
from django.contrib.auth.decorators import permission_required, login_required
from django.views import generic, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from catalog.models import Book, Author, BookInstance
from catalog.constants import LoanStatus, BOOKS_PER_PAGE, DEFAULT_RENEWAL_WEEKS
from catalog.forms import RenewBookForm


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.count()
    num_instances = BookInstance.objects.count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(
        status__exact=LoanStatus.AVAILABLE.value
    ).count()

    # Count of all authors
    num_authors = Author.objects.count()

    # Get the current numb of visits from the session (default 1 if not set),
    # then increment and save it back to track
    # how many times the user has visited the page.
    num_visits = request.session.get("num_visits", 1)
    request.session["num_visits"] = num_visits + 1

    context = {
        "num_books": num_books,
        "num_instances": num_instances,
        "num_instances_available": num_instances_available,
        "num_authors": num_authors,
        "num_visits": num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, "index.html", context=context)


class BookListView(generic.ListView):
    """Generic class-based view for a list of books."""

    model = Book
    paginate_by = BOOKS_PER_PAGE
    # your own name for the list as a template variable
    context_object_name = "book_list"
    # Specify your own template name/location
    template_name = "catalog/book_list.html"
    queryset = Book.objects.all().order_by("title")


class BookDetailView(generic.DetailView):
    """Generic class-based view for a book detail page."""

    model = Book

    def get_context_data(self, **kwargs):
        """Add additional context data to the view."""
        context = super(BookDetailView, self).get_context_data(**kwargs)
        context["AVAILABLE"] = LoanStatus.AVAILABLE.value
        context["ON_LOAN"] = LoanStatus.ON_LOAN.value
        context["RESERVED"] = LoanStatus.RESERVED.value
        context["MAINTENANCE"] = LoanStatus.MAINTENANCE.value
        context["book_instances"] = self.object.bookinstance_set.all()
        context["can_mark_returned"] = self.request.user.has_perm(
            "catalog.can_mark_returned"
        )
        return context

    def book_detali_view(self, primary_key):
        """View function for displaying a book detail page."""
        book = get_object_or_404(Book, pk=primary_key)

        return render(
            request, "catalog/book_detail.html", context={"book": book}
        )


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view for a list of books on loan to the current user.
    """

    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed_user.html"
    paginate_by = BOOKS_PER_PAGE

    def get_queryset(self):
        """Return the books on loan to the current user."""
        return (
            BookInstance.objects.filter(borrower=self.request.user)
            .filter(status__exact=LoanStatus.ON_LOAN.value)
            .order_by("due_back")
        )

    def get_context_data(self, **kwargs):
        """Add additional context data to the view."""
        context = super().get_context_data(**kwargs)
        context["can_renew"] = self.request.user.has_perm("catalog.can_renew")
        return context


class MarkBookAsReturnedView(PermissionRequiredMixin, View):
    """View for marking a book as returned."""

    permission_required = "catalog.can_mark_returned"

    def get(self, request, *args, **kwargs):
        """Display confirmation page."""
        book_instance = get_object_or_404(BookInstance, pk=kwargs["pk"])
        return render(
            request,
            "catalog/bookinstance_mark_as_returned.html",
            {
                "bookinstance": book_instance,
            },
        )

    def post(self, request, *args, **kwargs):
        """Process the form submission (confirm return)."""
        book_instance = get_object_or_404(BookInstance, pk=kwargs["pk"])
        book_instance.status = LoanStatus.AVAILABLE.value
        book_instance.borrower = None
        book_instance.save()

        # Redirect to the book detail page after returning
        return redirect("book-detail", pk=book_instance.book.pk)


@login_required
@permission_required("catalog.can_renew", raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a book instance by a librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == "POST":
        form = RenewBookForm(request.POST)
        if form.is_valid():
            # Process the renewal
            book_instance.due_back = form.cleaned_data["renewal_date"]
            book_instance.save()
            return redirect("my-borrowed")
    else:
        # Display the form with the current due date
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(
            weeks=DEFAULT_RENEWAL_WEEKS
        )
        form = RenewBookForm(initial={"renewal_date": proposed_renewal_date})

    context = {
        "form": form,
        "book_instance": book_instance,
    }

    return render(
        request,
        "catalog/book_renew_librarian.html",
        context,
    )


class AuthorListView(generic.ListView):
    """Generic class-based view for a list of authors."""

    model = Author
    paginate_by = BOOKS_PER_PAGE
    context_object_name = "author_list"
    template_name = "catalog/author_list.html"
    queryset = Author.objects.all().order_by("last_name", "first_name")

    def get_context_data(self, **kwargs):
        """Add additional context data to the view."""
        context = super(AuthorListView, self).get_context_data(**kwargs)
        context["can_add_author"] = self.request.user.has_perm(
            "catalog.can_add_author"
        )
        return context


class AuthorDetailView(generic.DetailView):
    """Generic class-based view for an author detail page."""

    model = Author

    def get_context_data(self, **kwargs):
        """Add additional context data to the view."""
        context = super(AuthorDetailView, self).get_context_data(**kwargs)
        context["book_set"] = Book.objects.filter(author=self.object).order_by(
            "title"
        )
        context["can_update_author"] = self.request.user.has_perm(
            "catalog.change_author"
        )
        context["can_delete_author"] = self.request.user.has_perm(
            "catalog.delete_author"
        )
        return context


class AuthorCreateView(PermissionRequiredMixin, CreateView):
    """Generic class-based view for creating a new author."""

    permission_required = "catalog.add_author"

    model = Author
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death"]
    initial = {
        "date_of_death": None,
    }


class AuthorUpdateView(PermissionRequiredMixin, UpdateView):
    """Generic class-based view for updating an existing author."""

    permission_required = "catalog.change_author"

    model = Author
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death"]

    def get_success_url(self):
        return reverse_lazy("author-detail", kwargs={"pk": self.object.pk})


class AuthorDeleteView(PermissionRequiredMixin, DeleteView):
    """Generic class-based view for deleting an author."""

    permission_required = "catalog.delete_author"

    model = Author
    success_url = reverse_lazy("authors")
