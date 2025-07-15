import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from catalog.constants import MAX_RENEWAL_WEEKS


class RenewBookForm(forms.Form):
    """Form for renewing a book instance."""

    renewal_date = forms.DateField(
        help_text=_("Enter a date between now and 4 weeks (default 3)."),
        widget=forms.widgets.DateInput(attrs={"type": "date"}),
    )

    def clean_renewal_date(self):
        """
        Check that the date is not in the past
        and not more than 4 weeks in the future.
        """
        data = self.cleaned_data["renewal_date"]
        if data < datetime.date.today():
            raise ValidationError(_("Invalid date - renewal in past"))
        if data > datetime.date.today() + datetime.timedelta(
            weeks=MAX_RENEWAL_WEEKS
        ):
            raise ValidationError(
                _("Invalid date - renewal " "more than 4 weeks ahead")
            )
        return data
