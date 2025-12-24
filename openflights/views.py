from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Airline, Airport, Country
from .serializers import (
    AirlineSerializer,
    AirportCreateSerializer,
    AirportSerializer,
    CountryWithCountsSerializer,
)


from django.conf import settings
import sys
import django
from pathlib import Path

from django.shortcuts import render, redirect
from .forms import AirportForm

def airport_form(request):
    if request.method == "POST":
        form = AirportForm(request.POST)
        if form.is_valid():
            airport = form.save()
            return redirect(f"/api/airports/{airport.airport_id}/")
    else:
        form = AirportForm()

    return render(request, "openflights/airport_form.html", {"form": form})

def index(request):
    req_path = Path(settings.BASE_DIR) / "requirements.txt"
    packages = req_path.read_text(encoding="utf-8") if req_path.exists() else "requirements.txt not found"

    html = f"""
    <h1>OpenFlights API</h1>

    <h2>Run info</h2>
    <ul>
      <li><b>Python</b>: {sys.version.split()[0]}</li>
      <li><b>Django</b>: {django.get_version()}</li>
    </ul>

    <h2>Packages</h2>
    <pre>{packages}</pre>

     

    <h2>REST Endpoints</h2>
    <ul>
      <li><a href="/api/airports/">GET /api/airports/</a></li>
      <li><a href="/api/countries/">GET /api/countries/</a></li>
      <li><a href="/api/airlines/">GET /api/airlines/</a></li>
      <li><a href="/api/airports/missing-codes/">GET /api/airports/missing-codes/</a></li>
      <li><a href="/api/countries/112/city-airport-counts/">GET /api/countries/&lt;id&gt;/city-airport-counts/</a></li>
      <li><a href="/api/airports/create/">POST /api/airports/create/</a></li>
      <li><a href="/api/airports/1001/">GET/PATCH/DELETE /api/airports/&lt;id&gt;/</a></li>
      <li><a href="/airport-form/">Django Form: Create Airport</a></li>
    </ul>
    """
    return HttpResponse(html)


@api_view(["GET"])
def country_city_airport_counts(request, country_id: int):
    qs = (
        Airport.objects.filter(country_id=country_id)
        .exclude(city__isnull=True)
        .exclude(city="")
        .values("city")
        .annotate(airport_count=Count("airport_id"))
        .order_by("-airport_count", "city")[:200]
    )
    return Response(list(qs))


@api_view(["GET"])
def airports_missing_codes(request):
    qs = Airport.objects.select_related("country").filter(
        Q(iata__isnull=True) | Q(iata="") | Q(icao__isnull=True) | Q(icao="")
    )

    country_id = request.query_params.get("country_id")
    if country_id:
        qs = qs.filter(country_id=country_id)

    qs = qs.order_by("airport_id")[:200]
    return Response(AirportSerializer(qs, many=True).data)


@api_view(["GET"])
def airlines_list(request):
    qs = Airline.objects.select_related("country").all()

    country_id = request.query_params.get("country_id")
    active = request.query_params.get("active")  # Y / N
    iata = request.query_params.get("iata")
    icao = request.query_params.get("icao")
    q = request.query_params.get("q")  # name contains

    if country_id:
        qs = qs.filter(country_id=country_id)
    if active:
        qs = qs.filter(active__iexact=active)
    if iata:
        qs = qs.filter(iata__iexact=iata)
    if icao:
        qs = qs.filter(icao__iexact=icao)
    if q:
        qs = qs.filter(name__icontains=q)

    qs = qs.order_by("airline_id")[:200]
    return Response(AirlineSerializer(qs, many=True).data)


@api_view(["GET"])
def countries_list(request):
    qs = Country.objects.all()

    q = request.query_params.get("q")
    if q:
        qs = qs.filter(name__icontains=q)

    qs = qs.annotate(
        airport_count=Count("airports", distinct=True),
        airline_count=Count("airlines", distinct=True),
    ).order_by("-airport_count", "name")[:200]

    return Response(CountryWithCountsSerializer(qs, many=True).data)


@api_view(["GET"])
def airports_list(request):
    qs = Airport.objects.select_related("country").all()

    country_id = request.query_params.get("country_id")
    city = request.query_params.get("city")
    iata = request.query_params.get("iata")
    icao = request.query_params.get("icao")
    q = request.query_params.get("q")  # name contains

    if country_id:
        qs = qs.filter(country_id=country_id)
    if city:
        qs = qs.filter(city__icontains=city)
    if iata:
        qs = qs.filter(iata__iexact=iata)
    if icao:
        qs = qs.filter(icao__iexact=icao)
    if q:
        qs = qs.filter(name__icontains=q)

    qs = qs.order_by("airport_id")[:200]  # cap for safety

    return Response(AirportSerializer(qs, many=True).data)


# create


@api_view(["POST"])
def airport_create(request):
    serializer = AirportCreateSerializer(data=request.data)
    if serializer.is_valid():
        airport = serializer.save()
        return Response(
            AirportSerializer(airport).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# update delete
@api_view(["GET", "PUT", "PATCH", "DELETE"])
def airport_detail(request, airport_id: int):
    airport = get_object_or_404(Airport, pk=airport_id)

    if request.method == "GET":
        return Response(AirportSerializer(airport).data)

    if request.method in ("PUT", "PATCH"):
        serializer = AirportCreateSerializer(
            airport,
            data=request.data,
            partial=(request.method == "PATCH"),
        )
        if serializer.is_valid():
            airport = serializer.save()
            return Response(
                AirportSerializer(airport).data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    airport.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
