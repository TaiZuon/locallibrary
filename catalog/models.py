"""catalog/models.py"""

import uuid  # Required for unique book instances
from datetime import date  # Used for date fields

from django.db import models

# Used to generate URLs by reversing the URL patterns
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from .constants import (
    MAX_LENGTH_TITLE,
    MAX_LENGTH_NAME,
    MAX_LENGTH_SUMMARY,
    MAX_LENGTH_ISBN,
    MAX_LENGTH_IMPRINT,
    LoanStatus,
)


class Genre(models.Model):
    """
    Model representing a book genre (e.g. Science Fiction, Non Fiction).
    """

    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        help_text=_("Enter a book genre (e.g. Science Fiction)"),
    )

    def __str__(self):
        """
        String for representing the Model object.
        """
        return self.name


class Book(models.Model):
    """
    Model representing a book (but not a specific copy of a book).
    """

    title = models.CharField(max_length=MAX_LENGTH_TITLE)

    # on_delete defines what happens when the related Book is deleted:
    # CASCADE: delete the BookInstance too
    # PROTECT: prevent deletion if related BookInstance exists
    # RESTRICT: similar to PROTECT (requires Django 3.1+)
    # SET_NULL: set book to NULL (requires null=True)
    # SET_DEFAULT: set to default value
    # DO_NOTHING: do nothing (can raise DB integrity errors)
    author = models.ForeignKey("Author", on_delete=models.SET_NULL, null=True)

    summary = models.TextField(
        max_length=MAX_LENGTH_SUMMARY,
        help_text=_("Enter a brief description of the book"),
    )
    isbn = models.CharField(
        "ISBN",
        max_length=MAX_LENGTH_ISBN,
        unique=True,
        help_text=_(
            '13 Character <a href="https://www.isbn-international.org/'
            'content/what-isbn">ISBN number</a>'
        ),
    )
    genre = models.ManyToManyField(
        Genre, help_text=_("Select a genre for this book")
    )

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.)
        """
        return self.title

    def get_absolute_url(self):
        """
        Returns the url to access a particular book instance.
        """
        return reverse("book-detail", args=[str(self.id)])

    def display_genre(self):
        """
        Creates a string for the Genre.
        This is required to display genre in Admin.
        """
        return ", ".join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = "Genre"


class BookInstance(models.Model):
    """
    Model representing a specific copy of a book
    (i.e. that can be borrowed from the library).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text=_("Unique ID for this particular book across whole library"),
    )

    # on_delete defines what happens when the related Book is deleted:
    # CASCADE: delete the BookInstance too
    # PROTECT: prevent deletion if related BookInstance exists
    # RESTRICT: similar to PROTECT (requires Django 3.1+)
    # SET_NULL: set book to NULL (requires null=True)
    # SET_DEFAULT: set to default value
    # DO_NOTHING: do nothing (can raise DB integrity errors)
    book = models.ForeignKey("Book", on_delete=models.RESTRICT)

    imprint = models.CharField(max_length=MAX_LENGTH_IMPRINT)
    due_back = models.DateField(null=True, blank=True)

    borrower = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    status = models.CharField(
        max_length=1,
        choices=[
            (
                LoanStatus.MAINTENANCE.value,
                _(str(LoanStatus.MAINTENANCE.name).capitalize()),
            ),
            (
                LoanStatus.ON_LOAN.value,
                _(str(LoanStatus.ON_LOAN.name).capitalize()),
            ),
            (
                LoanStatus.AVAILABLE.value,
                _(str(LoanStatus.AVAILABLE.name).capitalize()),
            ),
            (
                LoanStatus.RESERVED.value,
                _(str(LoanStatus.RESERVED.name).capitalize()),
            ),
        ],
        blank=True,
        default=LoanStatus.MAINTENANCE.value,
        help_text=_("Book availability"),
    )

    class Meta:
        ordering = ["due_back"]
        permissions = (
            ("can_mark_returned", _("Set book as returned")),
            ("can_renew", _("Renew a book")),
        )

    @property
    def is_overdue(self):
        """
        Checks if the book instance is overdue.
        """
        return self.due_back and date.today() > self.due_back

    def __str__(self):
        """
        String for representing the Model object.
        """
        return f"{self.id} ({self.book.title})"


class Author(models.Model):
    """
    Model representing an author.
    """

    first_name = models.CharField(max_length=MAX_LENGTH_NAME)
    last_name = models.CharField(max_length=MAX_LENGTH_NAME)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField(_("Died"), null=True, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def get_absolute_url(self):
        """
        Returns the url to access a particular author instance.
        """
        return reverse("author-detail", args=[str(self.id)])

    def __str__(self):
        """
        String for representing the Model object.
        """
        return f"{self.last_name}, {self.first_name}"
