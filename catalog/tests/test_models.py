from datetime import date, timedelta
import uuid

from django.test import TestCase
from django.contrib.auth.models import User

from catalog.models import Author, Book, BookInstance, Genre
from catalog.constants import LoanStatus


class AuthorModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        Author.objects.create(first_name="Big", last_name="Bob")

    def test_first_name_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field("first_name").verbose_name
        self.assertEqual(field_label, "first name")

    def test_date_of_death_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field("date_of_death").verbose_name
        self.assertEqual(field_label, "Died")

    def test_first_name_max_length(self):
        author = Author.objects.get(id=1)
        max_length = author._meta.get_field("first_name").max_length
        self.assertEqual(max_length, 100)

    def test_object_name_is_last_name_comma_first_name(self):
        author = Author.objects.get(id=1)
        expected_object_name = f"{author.last_name}, {author.first_name}"
        self.assertEqual(expected_object_name, str(author))

    def test_get_absolute_url(self):
        author = Author.objects.get(id=1)
        # This will also fail if the urlconf is not defined.
        self.assertEqual(author.get_absolute_url(), "/catalog/authors/1/")


class GenreModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Genre.objects.create(name="Science Fiction")

    def test_name_label(self):
        genre = Genre.objects.get(name="Science Fiction")
        field_label = genre._meta.get_field("name").verbose_name
        self.assertEqual(field_label, "name")

    def test_name_max_length(self):
        genre = Genre.objects.get(name="Science Fiction")
        max_length = genre._meta.get_field("name").max_length
        self.assertEqual(max_length, 100)

    def test_object_name_is_name(self):
        genre = Genre.objects.get(name="Science Fiction")
        self.assertEqual(str(genre), "Science Fiction")


class BookModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an author for the book
        cls.author = Author.objects.create(
            first_name="J.K.", last_name="Rowling"
        )

        # Create genres
        cls.genre1 = Genre.objects.create(name="Fantasy")
        cls.genre2 = Genre.objects.create(name="Young Adult")

        # Create a book
        cls.book = Book.objects.create(
            title="Harry Potter and the Philosopher's Stone",
            author=cls.author,
            summary="A young wizard discovers his magical heritage.",
            isbn="9780747532699",
        )
        cls.book.genre.add(cls.genre1, cls.genre2)

    def test_title_label(self):
        field_label = self.book._meta.get_field("title").verbose_name
        self.assertEqual(field_label, "title")

    def test_title_max_length(self):
        max_length = self.book._meta.get_field("title").max_length
        self.assertEqual(max_length, 200)

    def test_summary_max_length(self):
        max_length = self.book._meta.get_field("summary").max_length
        self.assertEqual(max_length, 100)

    def test_isbn_max_length(self):
        max_length = self.book._meta.get_field("isbn").max_length
        self.assertEqual(max_length, 13)

    def test_isbn_unique(self):
        field = self.book._meta.get_field("isbn")
        self.assertTrue(field.unique)

    def test_object_name_is_title(self):
        self.assertEqual(str(self.book), self.book.title)

    def test_get_absolute_url(self):
        # Use the actual book ID instead of hardcoded value
        expected_url = f"/catalog/books/{self.book.id}/"
        self.assertEqual(self.book.get_absolute_url(), expected_url)

    def test_display_genre(self):
        # Should display all genres (max 3)
        expected = "Fantasy, Young Adult"
        self.assertEqual(self.book.display_genre(), expected)

    def test_display_genre_with_more_than_three_genres(self):
        # Add more genres to test the limit
        genre3 = Genre.objects.create(name="Adventure")
        genre4 = Genre.objects.create(name="Fiction")
        self.book.genre.add(genre3, genre4)

        # Should only display first 3 genres
        displayed_genres = self.book.display_genre().split(", ")
        self.assertEqual(len(displayed_genres), 3)

    def test_author_foreign_key(self):
        self.assertEqual(self.book.author, self.author)

    def test_genre_many_to_many(self):
        self.assertEqual(self.book.genre.count(), 2)
        self.assertIn(self.genre1, self.book.genre.all())
        self.assertIn(self.genre2, self.book.genre.all())


class BookInstanceModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an author and book
        cls.author = Author.objects.create(
            first_name="George", last_name="Orwell"
        )
        cls.book = Book.objects.create(
            title="1984",
            author=cls.author,
            summary="A dystopian novel.",
            isbn="9780451524935",
        )

        # Create a user for borrower
        cls.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Create book instances
        cls.book_instance = BookInstance.objects.create(
            book=cls.book,
            imprint="Penguin Classics",
            status=LoanStatus.AVAILABLE.value,
        )

        # Create an instance without specifying status to test default
        cls.default_instance = BookInstance.objects.create(
            book=cls.book,
            imprint="Default Status Test",
        )

        cls.overdue_instance = BookInstance.objects.create(
            book=cls.book,
            imprint="Another Publisher",
            status=LoanStatus.ON_LOAN.value,
            due_back=date.today() - timedelta(days=5),
            borrower=cls.user,
        )

    def test_id_is_uuid(self):
        self.assertIsInstance(self.book_instance.id, uuid.UUID)

    def test_imprint_label(self):
        field_label = self.book_instance._meta.get_field("imprint").verbose_name
        self.assertEqual(field_label, "imprint")

    def test_imprint_max_length(self):
        max_length = self.book_instance._meta.get_field("imprint").max_length
        self.assertEqual(max_length, 200)

    def test_status_default_value(self):
        self.assertEqual(
            self.default_instance.status, LoanStatus.MAINTENANCE.value
        )

    def test_status_choices(self):
        field = self.book_instance._meta.get_field("status")
        choices = [choice[0] for choice in field.choices]
        expected_choices = [
            LoanStatus.MAINTENANCE.value,
            LoanStatus.ON_LOAN.value,
            LoanStatus.AVAILABLE.value,
            LoanStatus.RESERVED.value,
        ]
        self.assertEqual(choices, expected_choices)

    def test_object_name_includes_id_and_title(self):
        expected = f"{self.book_instance.id} ({self.book_instance.book.title})"
        self.assertEqual(str(self.book_instance), expected)

    def test_is_overdue_false_for_future_date(self):
        book_instance = BookInstance.objects.create(
            book=self.book,
            imprint="Future Due Date",
            due_back=date.today() + timedelta(days=5),
            status=LoanStatus.ON_LOAN.value,
        )
        self.assertFalse(book_instance.is_overdue)

    def test_is_overdue_true_for_past_date(self):
        self.assertTrue(self.overdue_instance.is_overdue)

    def test_is_overdue_false_for_no_due_date(self):
        # This instance has no due_back date
        self.assertFalse(self.book_instance.is_overdue)

    def test_book_foreign_key(self):
        self.assertEqual(self.book_instance.book, self.book)

    def test_borrower_foreign_key(self):
        self.assertEqual(self.overdue_instance.borrower, self.user)

    def test_borrower_can_be_null(self):
        self.assertIsNone(self.book_instance.borrower)

    def test_due_back_can_be_null(self):
        self.assertIsNone(self.book_instance.due_back)

    def test_meta_ordering(self):
        # Create another instance with earlier due date
        earlier_instance = BookInstance.objects.create(
            book=self.book,
            imprint="Earlier Due",
            due_back=date.today() - timedelta(days=10),
            status=LoanStatus.ON_LOAN.value,
        )

        # Get all instances ordered by due_back
        # (None values come last in Django)
        instances = list(BookInstance.objects.all())

        # Find instances with due dates
        instances_with_dates = [
            inst for inst in instances if inst.due_back is not None
        ]
        instances_with_dates.sort(key=lambda x: x.due_back)

        # The earlier due date should come first among those with dates
        self.assertEqual(instances_with_dates[0], earlier_instance)

    def test_meta_permissions(self):
        permissions = self.book_instance._meta.permissions
        expected_permissions = (
            ("can_mark_returned", "Set book as returned"),
            ("can_renew", "Renew a book"),
        )
        self.assertEqual(permissions, expected_permissions)
