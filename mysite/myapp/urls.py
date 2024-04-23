from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("ticker/<str:ticker>", views.ticker, name="ticker"),
    path("find/", views.find, name="find")
]
