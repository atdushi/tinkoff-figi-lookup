from django import forms


class FindTickerForm(forms.Form):
    name = forms.CharField(label="Type ticker", max_length=5)
