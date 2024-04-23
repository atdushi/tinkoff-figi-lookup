from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from .forms import FindTickerForm
import requests


# Create your views here.

def home(request):
    # return HttpResponse("hello world")
    return render(request, "home.html")


def ticker(request, ticker):
    response = requests.get(f"http://127.0.0.1:8001/ticker/{ticker}")
    return render(request, "ticker.html", {"figi": response.json()})


def find(request):
    if request.method == "GET":
        form = FindTickerForm()
        return render(request, "find.html", {"form": form})
    else:
        form = FindTickerForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            # return ticker(request, name)
            return HttpResponseRedirect(f"/ticker/{name}")
