'''catalog/views.py'''
from urllib import request

from django.shortcuts import render, get_object_or_404
from django.views import generic

from catalog.models import Book, Author, BookInstance
from catalog.constants import LoanStatus

from .constants import BOOKS_PER_PAGE

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.count()
    num_instances = BookInstance.objects.count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact=LoanStatus.AVAILABLE.value).count()

    # Count of all authors
    num_authors = Author.objects.count()  

    # Get the current number of visits from the session (default to 1 if not set),
    # then increment and save it back to track how many times the user has visited the page.
    num_visits = request.session.get('num_visits', 1)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class BookListView(generic.ListView):
    """Generic class-based view for a list of books."""

    model = Book
    paginate_by = BOOKS_PER_PAGE
    context_object_name = 'book_list'  # your own name for the list as a template variable
    template_name = 'catalog/book_list.html'  # Specify your own template name/location
    queryset = Book.objects.all().order_by('title')
    

class BookDetailView(generic.DetailView):
    """Generic class-based view for a book detail page."""
    model = Book

    def get_context_data(self, **kwargs):
        """Add additional context data to the view."""
        context = super(BookDetailView, self).get_context_data(**kwargs)
        context['LoanStatus'] = LoanStatus
        context['book_instances'] = self.object.bookinstance_set.all()
        return context

    def book_detali_view(self, primary_key):
        """View function for displaying a book detail page."""
        book = get_object_or_404(Book, pk=primary_key)

        return render(request, 'catalog/book_detail.html', context={'book': book})
