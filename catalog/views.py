"""catalog/views.py"""

from urllib import request

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import generic, View

from catalog.models import Book, Author, BookInstance
from catalog.constants import LoanStatus

from .constants import BOOKS_PER_PAGE


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


class LoanedBooksByUserListView(generic.ListView):
    """
    Generic class-based view for a list of books on loan to the current user.
    """

    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed_user.html"
    paginate_by = 5

    def get_queryset(self):
        """Return the books on loan to the current user."""
        return (
            BookInstance.objects.filter(borrower=self.request.user)
            .filter(status__exact=LoanStatus.ON_LOAN.value)
            .order_by("due_back")
        )


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
