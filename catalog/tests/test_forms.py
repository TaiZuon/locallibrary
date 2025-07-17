import datetime

from django import forms
from django.test import TestCase
from django.utils import timezone

from catalog.forms import RenewBookForm


class RenewBookFormTest(TestCase):
    def test_renew_form_date_field_label(self):
        form = RenewBookForm()
        self.assertTrue(
            form.fields["renewal_date"].label is None
            or form.fields["renewal_date"].label == "renewal date"
        )

    def test_renew_form_date_field_help_text(self):
        form = RenewBookForm()
        self.assertEqual(
            form.fields["renewal_date"].help_text,
            "Enter a date between now and 4 weeks (default 3).",
        )

    def test_renew_form_date_in_past(self):
        date = datetime.date.today() - datetime.timedelta(days=1)
        form = RenewBookForm(data={"renewal_date": date})
        self.assertFalse(form.is_valid())

    def test_renew_form_date_too_far_in_future(self):
        date = (
            datetime.date.today()
            + datetime.timedelta(weeks=4)
            + datetime.timedelta(days=1)
        )
        form = RenewBookForm(data={"renewal_date": date})
        self.assertFalse(form.is_valid())

    def test_renew_form_date_today(self):
        date = datetime.date.today()
        form = RenewBookForm(data={"renewal_date": date})
        self.assertTrue(form.is_valid())

    def test_renew_form_date_max(self):
        date = timezone.localtime().date() + datetime.timedelta(weeks=4)
        form = RenewBookForm(data={"renewal_date": date})
        self.assertTrue(form.is_valid())

    def test_renew_form_date_exactly_four_weeks(self):
        """Test that exactly 4 weeks from today is valid."""
        date = datetime.date.today() + datetime.timedelta(weeks=4)
        form = RenewBookForm(data={"renewal_date": date})
        self.assertTrue(form.is_valid())

    def test_renew_form_empty_data(self):
        """Test form with no data (should be invalid)."""
        form = RenewBookForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("renewal_date", form.errors)

    def test_renew_form_invalid_date_format(self):
        """Test form with invalid date format."""
        form = RenewBookForm(data={"renewal_date": "invalid-date"})
        self.assertFalse(form.is_valid())

    def test_renew_form_widget_type(self):
        """Test that the form uses date input widget."""
        form = RenewBookForm()
        widget = form.fields["renewal_date"].widget
        self.assertIsInstance(widget, forms.widgets.DateInput)
        # Test that the widget has the correct HTML input type
        html_output = widget.render("test", None)
        self.assertIn('type="date"', html_output)
