'''Django management command to seed the database with test data.'''
import random
import uuid

from django.core.management.base import BaseCommand
from django_seed import Seed

from catalog.models import Author, Book, Genre, BookInstance
from catalog.constants import LoanStatus


class Command(BaseCommand):
    """Django management command to seed the database with test data."""
    help = 'Seed database with test data'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete all seeded data')

    def handle(self, *args, **kwargs):
        if kwargs['clear']:
            self.stdout.write('🧹 Clearing seeded data...')
            BookInstance.objects.all().delete()
            Book.objects.all().delete()
            Author.objects.all().delete()
            Genre.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✅ All seeded data deleted.'))
            return

        seeder = Seed.seeder()

        # Clear existing data if needed
        Genre.objects.all().delete()
        Author.objects.all().delete()
        Book.objects.all().delete()
        BookInstance.objects.all().delete()

        # Seed genres
        genre_names = ['Science Fiction', 'Fantasy', 'Mystery', 'Romance', 'Non-Fiction']
        genres = [Genre.objects.create(name=name) for name in genre_names]

        # Seed authors
        seeder.add_entity(Author, 10, {
            'first_name': lambda x: seeder.faker.first_name(),
            'last_name': lambda x: seeder.faker.last_name(),
            'date_of_birth': lambda x: seeder.faker.date_of_birth(minimum_age=30, maximum_age=80),
            'date_of_death': lambda x: None
        })

        inserted_pks = seeder.execute()
        authors = Author.objects.all()

        # Seed books manually to set M2M and FK
        books = []
        for _ in range(20):
            book = Book.objects.create(
                title=seeder.faker.sentence(nb_words=4),
                summary=seeder.faker.text(max_nb_chars=200),
                isbn=seeder.faker.isbn13(separator=""),
                author=random.choice(authors),
            )
            # Assign 1–3 genres
            book.genre.set(random.sample(genres, k=random.randint(1, 3)))
            books.append(book)

        # Seed book instances
        for book in books:
            for _ in range(random.randint(1, 5)):  # 1–5 copies
                BookInstance.objects.create(
                    id=uuid.uuid4(),
                    book=book,
                    imprint=seeder.faker.company(),
                    due_back=seeder.faker.date_between(start_date='today', end_date='+30d'),
                    status=random.choice([status.value for status in LoanStatus])
                )

        self.stdout.write(self.style.SUCCESS('🎉 Database seeded successfully!'))
