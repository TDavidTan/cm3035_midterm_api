from django.db import models

# Create your models here.


class Country(models.Model):
    country_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=120)
    iso2 = models.CharField(max_length=2, null=True, blank=True)
    dafif = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.name


class Airport(models.Model):
    airport_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=120, null=True, blank=True)

    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        db_column="country_id",
        related_name="airports",
    )

    iata = models.CharField(max_length=3, null=True, blank=True)
    icao = models.CharField(max_length=4, null=True, blank=True)

    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    altitude_ft = models.IntegerField(null=True, blank=True)

    timezone_hrs = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    dst = models.CharField(max_length=1, null=True, blank=True)
    tz = models.CharField(max_length=60, null=True, blank=True)

    type = models.CharField(max_length=50, null=True, blank=True)
    source = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.iata or '—'})"


class Airline(models.Model):
    airline_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    alias = models.CharField(max_length=200, null=True, blank=True)
    iata = models.CharField(max_length=3, null=True, blank=True)
    icao = models.CharField(max_length=4, null=True, blank=True)
    callsign = models.CharField(max_length=120, null=True, blank=True)

    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        db_column="country_id",
        related_name="airlines",
    )

    active = models.CharField(max_length=1, null=True, blank=True)  # 'Y'/'N'

    def __str__(self):
        return self.name


class Plane(models.Model):
    plane_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    iata = models.CharField(max_length=3, null=True, blank=True)
    icao = models.CharField(max_length=4, null=True, blank=True)

    def __str__(self):
        return self.name
