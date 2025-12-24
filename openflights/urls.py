from django.urls import path

from . import views

urlpatterns = [
    path("airports/", views.airports_list, name="airports_list"),
    path("countries/", views.countries_list, name="countries_list"),
    path("airlines/", views.airlines_list, name="airlines_list"),
    path(
        "airports/missing-codes/",
        views.airports_missing_codes,
        name="airports_missing_codes",
    ),
    path(
        "countries/<int:country_id>/city-airport-counts/",
        views.country_city_airport_counts,
        name="country_city_airport_counts",
    ),
    # create
    path("airports/create/", views.airport_create, name="airport_create"),
    # update delete
    path("airports/<int:airport_id>/", views.airport_detail, name="airport_detail"),
]
