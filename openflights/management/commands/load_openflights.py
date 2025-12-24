import csv
import os
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from openflights.models import Airline, Airport, Country, Plane


def norm(v: str):
    """Convert OpenFlights-style missing values to None."""
    if v is None:
        return None
    v = v.strip()
    return None if v == "" or v == r"\N" else v


def to_int(v: str):
    v = norm(v)
    return int(v) if v is not None else None


def to_decimal(v: str):
    v = norm(v)
    if v is None:
        return None
    try:
        return Decimal(v)
    except (InvalidOperation, ValueError):
        return None


class Command(BaseCommand):
    help = (
        "Bulk load OpenFlights CSVs (countries, airports, airlines, planes) "
        "into SQLite."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            default="data",
            help=(
                "Directory containing countries.csv, airports.csv, "
                "airlines.csv, planes.csv"
            ),
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing rows before loading (useful during development).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        data_dir = options["data_dir"]
        clear = options["clear"]

        required = ["countries.csv", "airports.csv", "airlines.csv", "planes.csv"]
        for f in required:
            path = os.path.join(data_dir, f)
            if not os.path.exists(path):
                raise CommandError(f"Missing file: {path}")

        if clear:
            self.stdout.write("Clearing existing data...")
            Airport.objects.all().delete()
            Airline.objects.all().delete()
            Plane.objects.all().delete()
            Country.objects.all().delete()

        self.load_countries(os.path.join(data_dir, "countries.csv"))
        self.load_planes(os.path.join(data_dir, "planes.csv"))
        self.load_airports(os.path.join(data_dir, "airports.csv"))
        self.load_airlines(os.path.join(data_dir, "airlines.csv"))

        total = (
            Country.objects.count()
            + Airport.objects.count()
            + Airline.objects.count()
            + Plane.objects.count()
        )
        self.stdout.write(self.style.SUCCESS("Load complete."))
        self.stdout.write(
            f"Countries={Country.objects.count()}, "
            f"Airports={Airport.objects.count()}, "
            f"Airlines={Airline.objects.count()}, "
            f"Planes={Plane.objects.count()}, Total={total}"
        )

        # Important: midterm hard rule
        if total > 10000:
            raise CommandError(
                f"Total rows {total} exceeds 10,000 limit. Reduce dataset."
            )

    def load_countries(self, path):
        self.stdout.write(f"Loading countries from {path} ...")
        objs = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                objs.append(
                    Country(
                        country_id=int(row["country_id"]),
                        name=row["name"].strip(),
                        iso2=norm(row.get("iso2")),
                        dafif=norm(row.get("dafif")),
                    )
                )
        Country.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f"  inserted {len(objs)} countries")

    def load_planes(self, path):
        self.stdout.write(f"Loading planes from {path} ...")
        objs = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                objs.append(
                    Plane(
                        plane_id=int(row["plane_id"]),
                        name=row["name"].strip(),
                        iata=norm(row.get("iata")),
                        icao=norm(row.get("icao")),
                    )
                )
        Plane.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f"  inserted {len(objs)} planes")

    def load_airports(self, path):
        self.stdout.write(f"Loading airports from {path} ...")
        objs = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                country_id = to_int(row.get("country_id"))
                if country_id is None:
                    continue  # should not happen, but be safe

                objs.append(
                    Airport(
                        airport_id=int(row["airport_id"]),
                        name=row["name"].strip(),
                        city=norm(row.get("city")),
                        country_id=country_id,
                        iata=norm(row.get("iata")),
                        icao=norm(row.get("icao")),
                        latitude=to_decimal(row.get("latitude")),
                        longitude=to_decimal(row.get("longitude")),
                        altitude_ft=to_int(row.get("altitude_ft")),
                        timezone_hrs=to_decimal(row.get("timezone_hrs")),
                        dst=norm(row.get("dst")),
                        tz=norm(row.get("tz")),
                        type=norm(row.get("type")),
                        source=norm(row.get("source")),
                    )
                )
        Airport.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f"  inserted {len(objs)} airports")

    def load_airlines(self, path):
        self.stdout.write(f"Loading airlines from {path} ...")
        objs = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                country_id = to_int(row.get("country_id"))
                if country_id is None:
                    continue

                objs.append(
                    Airline(
                        airline_id=int(row["airline_id"]),
                        name=row["name"].strip(),
                        alias=norm(row.get("alias")),
                        iata=norm(row.get("iata")),
                        icao=norm(row.get("icao")),
                        callsign=norm(row.get("callsign")),
                        country_id=country_id,
                        active=norm(row.get("active")),
                    )
                )
        Airline.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f"  inserted {len(objs)} airlines")
