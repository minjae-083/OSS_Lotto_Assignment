from django import forms

from .services import validate_numbers


class ManualTicketForm(forms.Form):
    n1 = forms.IntegerField(min_value=1, max_value=45, label="1번")
    n2 = forms.IntegerField(min_value=1, max_value=45, label="2번")
    n3 = forms.IntegerField(min_value=1, max_value=45, label="3번")
    n4 = forms.IntegerField(min_value=1, max_value=45, label="4번")
    n5 = forms.IntegerField(min_value=1, max_value=45, label="5번")
    n6 = forms.IntegerField(min_value=1, max_value=45, label="6번")

    def clean(self):
        cleaned = super().clean()
        nums = [cleaned.get(f"n{i}") for i in range(1, 7)]
        if all(n is not None for n in nums):
            try:
                validate_numbers(nums)
            except Exception as exc:
                raise forms.ValidationError(str(exc))
            cleaned["numbers"] = sorted(nums)
        return cleaned
