from django import forms
from .models import Airport, Country


class AirportForm(forms.ModelForm):
    class Meta:
        model = Airport
        fields = ["airport_id", "name", "city", "country", "iata", "icao"]

    def clean_iata(self):
        value = self.cleaned_data.get("iata")
        if value:
            value = value.strip().upper()
            if len(value) != 3:
                raise forms.ValidationError("IATA code must be exactly 3 characters.")
        return value

    def clean_icao(self):
        value = self.cleaned_data.get("icao")
        if value:
            value = value.strip().upper()
            if len(value) != 4:
                raise forms.ValidationError("ICAO code must be exactly 4 characters.")
        return value