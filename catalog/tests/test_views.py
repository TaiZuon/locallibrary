import datetime
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from catalog.models import Author, Book, BookInstance, Genre
from catalog.constants import BOOKS_PER_PAGE, LoanStatus, DEFAULT_RENEWAL_WEEKS
from catalog.forms import RenewBookForm


class IndexViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test data
        cls.author = Author.objects.create(
            first_name="Test", last_name="Author"
        )
        cls.genre = Genre.objects.create(name="Fantasy")
        cls.book = Book.objects.create(
            title="Test Book",
            author=cls.author,
            summary="Test summary",
            isbn="1234567890123",
        )
        cls.book.genre.add(cls.genre)

        # Create book instances with different statuses
        BookInstance.objects.create(
            book=cls.book,
            imprint="Test Publisher",
            status=LoanStatus.AVAILABLE.value,
        )
        BookInstance.objects.create(
            book=cls.book,
            imprint="Test Publisher 2",
            status=LoanStatus.ON_LOAN.value,
        )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/catalog/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")

    def test_context_contains_counts(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

        # Check that context contains the expected counts
        self.assertIn("num_books", response.context)
        self.assertIn("num_instances", response.context)
        self.assertIn("num_instances_available", response.context)
        self.assertIn("num_authors", response.context)
        self.assertIn("num_visits", response.context)

        # Check actual counts
        self.assertEqual(response.context["num_books"], 1)
        self.assertEqual(response.context["num_instances"], 2)
        self.assertEqual(response.context["num_instances_available"], 1)
        self.assertEqual(response.context["num_authors"], 1)

    def test_visit_counter_increments(self):
        # First visit
        response1 = self.client.get(reverse("index"))
        self.assertEqual(response1.context["num_visits"], 1)

        # Second visit
        response2 = self.client.get(reverse("index"))
        self.assertEqual(response2.context["num_visits"], 2)


class BookListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(
            first_name="Test", last_name="Author"
        )

        # Create books for pagination test
        number_of_books = BOOKS_PER_PAGE + 2
        for book_id in range(number_of_books):
            Book.objects.create(
                title=f"Book {book_id}",
                author=cls.author,
                summary="Test summary",
                isbn=f"123456789012{book_id}",
            )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/catalog/books/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("books"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("books"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/book_list.html")

    def test_pagination_is_correct(self):
        response = self.client.get(reverse("books"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertTrue(response.context["is_paginated"] is True)
        self.assertTrue(len(response.context["book_list"]) == BOOKS_PER_PAGE)

    def test_books_ordered_by_title(self):
        response = self.client.get(reverse("books"))
        self.assertEqual(response.status_code, 200)
        books = response.context["book_list"]

        # Check that books are ordered by title
        for i in range(len(books) - 1):
            self.assertLessEqual(books[i].title, books[i + 1].title)


class BookDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(
            first_name="Test", last_name="Author"
        )
        cls.book = Book.objects.create(
            title="Test Book",
            author=cls.author,
            summary="Test summary",
            isbn="1234567890123",
        )
        cls.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        cls.book_instance = BookInstance.objects.create(
            book=cls.book,
            imprint="Test Publisher",
            status=LoanStatus.AVAILABLE.value,
        )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f"/catalog/books/{self.book.id}/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(
            reverse("book-detail", kwargs={"pk": self.book.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(
            reverse("book-detail", kwargs={"pk": self.book.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/book_detail.html")

    def test_context_contains_loan_status_constants(self):
        response = self.client.get(
            reverse("book-detail", kwargs={"pk": self.book.pk})
        )
        self.assertEqual(response.status_code, 200)

        # Check that loan status constants are in context
        self.assertIn("AVAILABLE", response.context)
        self.assertIn("ON_LOAN", response.context)
        self.assertIn("RESERVED", response.context)
        self.assertIn("MAINTENANCE", response.context)
        self.assertIn("book_instances", response.context)

    def test_context_contains_book_instances(self):
        response = self.client.get(
            reverse("book-detail", kwargs={"pk": self.book.pk})
        )
        self.assertEqual(response.status_code, 200)

        # Check that book instances are included
        book_instances = response.context["book_instances"]
        self.assertEqual(len(book_instances), 1)
        self.assertEqual(book_instances[0], self.book_instance)

    def test_404_for_invalid_book(self):
        response = self.client.get(reverse("book-detail", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)


class LoanedBooksByUserListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test users
        cls.user1 = User.objects.create_user(
            username="testuser1", password="testpass123"
        )
        cls.user2 = User.objects.create_user(
            username="testuser2", password="testpass123"
        )

        # Create test data
        cls.author = Author.objects.create(
            first_name="Test", last_name="Author"
        )
        cls.book = Book.objects.create(
            title="Test Book",
            author=cls.author,
            summary="Test summary",
            isbn="1234567890123",
        )

        # Create book instances for different users
        cls.book_instance1 = BookInstance.objects.create(
            book=cls.book,
            imprint="Test Publisher 1",
            status=LoanStatus.ON_LOAN.value,
            borrower=cls.user1,
            due_back=datetime.date.today() + datetime.timedelta(days=5),
        )
        cls.book_instance2 = BookInstance.objects.create(
            book=cls.book,
            imprint="Test Publisher 2",
            status=LoanStatus.ON_LOAN.value,
            borrower=cls.user2,
            due_back=datetime.date.today() + datetime.timedelta(days=10),
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("my-borrowed"))
        self.assertRedirects(
            response, "/accounts/login/?next=/catalog/mybooks/"
        )

    def test_logged_in_uses_correct_template(self):
        self.client.login(username="testuser1", password="testpass123")
        response = self.client.get(reverse("my-borrowed"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "catalog/bookinstance_list_borrowed_user.html"
        )

    def test_only_borrowed_books_in_list(self):
        self.client.login(username="testuser1", password="testpass123")
        response = self.client.get(reverse("my-borrowed"))
        self.assertEqual(response.status_code, 200)

        # Check that only user1's borrowed books are shown
        bookinstance_list = response.context["bookinstance_list"]
        self.assertEqual(len(bookinstance_list), 1)
        self.assertEqual(bookinstance_list[0], self.book_instance1)

    def test_books_ordered_by_due_date(self):
        # Create another book for user1
        book_instance3 = BookInstance.objects.create(
            book=self.book,
            imprint="Test Publisher 3",
            status=LoanStatus.ON_LOAN.value,
            borrower=self.user1,
            due_back=datetime.date.today() + datetime.timedelta(days=2),
        )

        self.client.login(username="testuser1", password="testpass123")
        response = self.client.get(reverse("my-borrowed"))
        self.assertEqual(response.status_code, 200)

        bookinstance_list = response.context["bookinstance_list"]
        self.assertEqual(len(bookinstance_list), 2)
        # Should be ordered by due_back (earliest first)
        self.assertEqual(bookinstance_list[0], book_instance3)
        self.assertEqual(bookinstance_list[1], self.book_instance1)


class RenewBookLibrarianViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a user with permissions
        cls.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Add the renewal permission
        content_type = ContentType.objects.get_for_model(BookInstance)
        permission = Permission.objects.get(
            codename="can_renew",
            content_type=content_type,
        )
        cls.user.user_permissions.add(permission)

        # Create test data
        cls.author = Author.objects.create(
            first_name="Test", last_name="Author"
        )
        cls.book = Book.objects.create(
            title="Test Book",
            author=cls.author,
            summary="Test summary",
            isbn="1234567890123",
        )
        cls.book_instance = BookInstance.objects.create(
            book=cls.book,
            imprint="Test Publisher",
            status=LoanStatus.ON_LOAN.value,
            borrower=cls.user,
            due_back=datetime.date.today() + datetime.timedelta(days=5),
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(
            reverse(
                "renew-book-librarian", kwargs={"pk": self.book_instance.pk}
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_forbidden_if_no_permission(self):
        user_no_perm = User.objects.create_user(
            username="noperm", password="test"
        )
        self.client.login(username="noperm", password="test")
        response = self.client.get(
            reverse(
                "renew-book-librarian", kwargs={"pk": self.book_instance.pk}
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_logged_in_with_permission_can_access(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "renew-book-librarian", kwargs={"pk": self.book_instance.pk}
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "renew-book-librarian", kwargs={"pk": self.book_instance.pk}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/book_renew_librarian.html")

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "renew-book-librarian", kwargs={"pk": self.book_instance.pk}
            )
        )
        self.assertEqual(response.status_code, 200)

        date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(
            weeks=DEFAULT_RENEWAL_WEEKS
        )
        self.assertEqual(
            response.context["form"].initial["renewal_date"],
            date_3_weeks_in_future,
        )

    def test_form_invalid_renewal_date_past(self):
        self.client.login(username="testuser", password="testpass123")
        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
        response = self.client.post(
            reverse(
                "renew-book-librarian", kwargs={"pk": self.book_instance.pk}
            ),
            {"renewal_date": date_in_past},
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Invalid date - renewal in past", form.errors["renewal_date"]
        )

    def test_form_invalid_renewal_date_future(self):
        self.client.login(username="testuser", password="testpass123")
        date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        response = self.client.post(
            reverse(
                "renew-book-librarian", kwargs={"pk": self.book_instance.pk}
            ),
            {"renewal_date": date_in_future},
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Invalid date - renewal more than 4 weeks ahead",
            form.errors["renewal_date"],
        )

    def test_form_valid_renewal_date_redirects_to_book_detail(self):
        self.client.login(username="testuser", password="testpass123")
        valid_date_in_future = datetime.date.today() + datetime.timedelta(
            weeks=2
        )
        response = self.client.post(
            reverse(
                "renew-book-librarian", kwargs={"pk": self.book_instance.pk}
            ),
            {"renewal_date": valid_date_in_future},
        )
        self.assertRedirects(
            response,
            reverse("book-detail", kwargs={"pk": self.book_instance.book.pk}),
        )

    def test_form_valid_renewal_date_updates_book_instance(self):
        self.client.login(username="testuser", password="testpass123")
        valid_date_in_future = datetime.date.today() + datetime.timedelta(
            weeks=2
        )
        response = self.client.post(
            reverse(
                "renew-book-librarian", kwargs={"pk": self.book_instance.pk}
            ),
            {"renewal_date": valid_date_in_future},
        )

        # Check that the book instance was updated
        self.book_instance.refresh_from_db()
        self.assertEqual(self.book_instance.due_back, valid_date_in_future)

    def test_404_for_invalid_book_instance(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "renew-book-librarian",
                kwargs={"pk": "99999999-9999-9999-9999-999999999999"},
            )
        )
        self.assertEqual(response.status_code, 404)


class AuthorDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(
            first_name="Test",
            last_name="Author",
            date_of_birth=datetime.date(1990, 1, 1),
        )
        cls.book = Book.objects.create(
            title="Test Book",
            author=cls.author,
            summary="Test summary",
            isbn="1234567890123",
        )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f"/catalog/authors/{self.author.id}/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(
            reverse("author-detail", kwargs={"pk": self.author.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(
            reverse("author-detail", kwargs={"pk": self.author.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/author_detail.html")

    def test_context_contains_author_books(self):
        response = self.client.get(
            reverse("author-detail", kwargs={"pk": self.author.pk})
        )
        self.assertEqual(response.status_code, 200)

        # Check that author's books are included
        book_set = response.context["book_set"]
        self.assertEqual(len(book_set), 1)
        self.assertEqual(book_set[0], self.book)

    def test_404_for_invalid_author(self):
        response = self.client.get(
            reverse("author-detail", kwargs={"pk": 99999})
        )
        self.assertEqual(response.status_code, 404)


class AuthorCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Add the add_author permission
        content_type = ContentType.objects.get_for_model(Author)
        permission = Permission.objects.get(
            codename="add_author",
            content_type=content_type,
        )
        cls.user.user_permissions.add(permission)

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("author-create"))
        self.assertEqual(response.status_code, 302)

    def test_forbidden_if_no_permission(self):
        user_no_perm = User.objects.create_user(
            username="noperm", password="test"
        )
        self.client.login(username="noperm", password="test")
        response = self.client.get(reverse("author-create"))
        self.assertEqual(response.status_code, 403)

    def test_logged_in_with_permission_can_access(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("author-create"))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("author-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/author_form.html")

    def test_form_create_author_redirects_to_detail_view(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("author-create"),
            {
                "first_name": "New",
                "last_name": "Author",
                "date_of_birth": "1990-01-01",
            },
        )

        # Should redirect to the new author's detail page
        author = Author.objects.get(first_name="New", last_name="Author")
        self.assertRedirects(
            response, reverse("author-detail", kwargs={"pk": author.pk})
        )


class AuthorUpdateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Add the change_author permission
        content_type = ContentType.objects.get_for_model(Author)
        permission = Permission.objects.get(
            codename="change_author",
            content_type=content_type,
        )
        cls.user.user_permissions.add(permission)

        cls.author = Author.objects.create(
            first_name="Test",
            last_name="Author",
            date_of_birth=datetime.date(1990, 1, 1),
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(
            reverse("author-update", kwargs={"pk": self.author.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_forbidden_if_no_permission(self):
        user_no_perm = User.objects.create_user(
            username="noperm", password="test"
        )
        self.client.login(username="noperm", password="test")
        response = self.client.get(
            reverse("author-update", kwargs={"pk": self.author.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_logged_in_with_permission_can_access(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("author-update", kwargs={"pk": self.author.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("author-update", kwargs={"pk": self.author.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/author_form.html")

    def test_form_update_author_redirects_to_detail_view(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("author-update", kwargs={"pk": self.author.pk}),
            {
                "first_name": "Updated",
                "last_name": "Author",
                "date_of_birth": "1990-01-01",
            },
        )

        self.assertRedirects(
            response, reverse("author-detail", kwargs={"pk": self.author.pk})
        )

        # Check that the author was updated
        self.author.refresh_from_db()
        self.assertEqual(self.author.first_name, "Updated")


class AuthorDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Add the delete_author permission
        content_type = ContentType.objects.get_for_model(Author)
        permission = Permission.objects.get(
            codename="delete_author",
            content_type=content_type,
        )
        cls.user.user_permissions.add(permission)

        cls.author = Author.objects.create(
            first_name="Test",
            last_name="Author",
            date_of_birth=datetime.date(1990, 1, 1),
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(
            reverse("author-delete", kwargs={"pk": self.author.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_forbidden_if_no_permission(self):
        user_no_perm = User.objects.create_user(
            username="noperm", password="test"
        )
        self.client.login(username="noperm", password="test")
        response = self.client.get(
            reverse("author-delete", kwargs={"pk": self.author.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_logged_in_with_permission_can_access(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("author-delete", kwargs={"pk": self.author.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("author-delete", kwargs={"pk": self.author.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/author_confirm_delete.html")

    def test_form_delete_author_redirects_to_list_view(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("author-delete", kwargs={"pk": self.author.pk})
        )

        self.assertRedirects(response, reverse("authors"))

        # Check that the author was deleted
        self.assertFalse(Author.objects.filter(pk=self.author.pk).exists())


class AuthorListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create authors for pagination tests (BOOKS_PER_PAGE + 3 = 8 total)
        number_of_authors = BOOKS_PER_PAGE + 3
        for author_id in range(number_of_authors):
            Author.objects.create(
                first_name=f"Christian {author_id}",
                last_name=f"Surname {author_id}",
            )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/catalog/authors/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("authors"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("authors"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/author_list.html")

    def test_pagination_items_per_page(self):
        response = self.client.get(reverse("authors"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertTrue(response.context["is_paginated"] is True)
        self.assertTrue(len(response.context["author_list"]) == BOOKS_PER_PAGE)

    def test_lists_all_authors(self):
        # Get second page and confirm it has (exactly) remaining 3 items
        response = self.client.get(reverse("authors") + "?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertTrue(response.context["is_paginated"] is True)
        self.assertTrue(len(response.context["author_list"]) == 3)
