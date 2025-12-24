from rest_framework import serializers

from .models import Airline, Airport, Country, Plane


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["country_id", "name", "iso2", "dafif"]


class AirportSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Airport
        fields = [
            "airport_id",
            "name",
            "city",
            "country_id",
            "country_name",
            "iata",
            "icao",
            "latitude",
            "longitude",
            "altitude_ft",
            "timezone_hrs",
            "dst",
            "tz",
            "type",
            "source",
        ]


class AirlineSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Airline
        fields = [
            "airline_id",
            "name",
            "alias",
            "iata",
            "icao",
            "callsign",
            "country_id",
            "country_name",
            "active",
        ]


class PlaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plane
        fields = ["plane_id", "name", "iata", "icao"]


class CountryWithCountsSerializer(serializers.ModelSerializer):
    airport_count = serializers.IntegerField(read_only=True)
    airline_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Country
        fields = [
            "country_id",
            "name",
            "iso2",
            "dafif",
            "airport_count",
            "airline_count",
        ]


# create


class AirportCreateSerializer(serializers.ModelSerializer):
    country_id = serializers.IntegerField(write_only=True)
    # airport_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Airport
        fields = [
            "airport_id",
            "name",
            "city",
            "country_id",
            "iata",
            "icao",
            "latitude",
            "longitude",
            "altitude_ft",
            "timezone_hrs",
            "dst",
            "tz",
            "type",
            "source",
        ]

    def validate_country_id(self, value):
        if not Country.objects.filter(pk=value).exists():
            raise serializers.ValidationError("country_id does not exist.")
        return value

    def validate_iata(self, value):
        if value in (None, ""):
            return value
        if len(value) != 3:
            raise serializers.ValidationError("IATA code must be exactly 3 characters.")
        return value.upper()

    def validate_icao(self, value):
        if value in (None, ""):
            return value
        if len(value) != 4:
            raise serializers.ValidationError("ICAO code must be exactly 4 characters.")
        return value.upper()

    def create(self, validated_data):
        country_id = validated_data.pop("country_id")
        return Airport.objects.create(country_id=country_id, **validated_data)

    def update(self, instance, validated_data):
        if "country_id" in validated_data:
            instance.country_id = validated_data.pop("country_id")
        return super().update(instance, validated_data)
