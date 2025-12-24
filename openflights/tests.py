from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Airline, Airport, Country


class OpenFlightsAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Countries
        cls.dk = Country.objects.create(
            country_id=112, name="Denmark", iso2="DK", dafif="DA"
        )
        cls.th = Country.objects.create(
            country_id=274, name="Thailand", iso2="TH", dafif="TH"
        )

        # Airports (include: normal, missing codes, multiple same city for aggregation)
        Airport.objects.create(
            airport_id=1001,
            name="Copenhagen Airport",
            city="Copenhagen",
            country=cls.dk,
            iata="CPH",
            icao="EKCH",
            latitude=55.6181,
            longitude=12.6560,
            altitude_ft=17,
            timezone_hrs=1,
            dst="E",
            tz="Europe/Copenhagen",
            type="airport",
            source="test",
        )
        Airport.objects.create(
            airport_id=1002,
            name="Test Missing Codes",
            city="Copenhagen",
            country=cls.dk,
            iata=None,
            icao=None,
            latitude=55.0,
            longitude=12.0,
            altitude_ft=10,
            timezone_hrs=1,
            dst="E",
            tz="Europe/Copenhagen",
            type="airport",
            source="test",
        )
        Airport.objects.create(
            airport_id=1003,
            name="Bangkok Airport A",
            city="Bangkok",
            country=cls.th,
            iata="BKA",
            icao="VTBA",
            latitude=13.7,
            longitude=100.5,
            altitude_ft=5,
            timezone_hrs=7,
            dst="N",
            tz="Asia/Bangkok",
            type="airport",
            source="test",
        )
        Airport.objects.create(
            airport_id=1004,
            name="Bangkok Airport B",
            city="Bangkok",
            country=cls.th,
            iata="BKB",
            icao="VTBB",
            latitude=13.8,
            longitude=100.6,
            altitude_ft=6,
            timezone_hrs=7,
            dst="N",
            tz="Asia/Bangkok",
            type="airport",
            source="test",
        )

        # Airlines
        Airline.objects.create(
            airline_id=2001,
            name="Test Air DK",
            alias=None,
            iata="TD",
            icao="TDK",
            callsign="TESTDK",
            country=cls.dk,
            active="Y",
        )
        Airline.objects.create(
            airline_id=2002,
            name="Test Air TH",
            alias=None,
            iata="TT",
            icao="TTH",
            callsign="TESTTH",
            country=cls.th,
            active="N",
        )

    def test_get_airports_list(self):
        url = reverse("airports_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.json(), list)
        self.assertGreaterEqual(len(resp.json()), 1)

    def test_get_airports_filter_by_iata(self):
        url = reverse("airports_list")
        resp = self.client.get(url, {"iata": "CPH"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["iata"], "CPH")

    def test_get_countries_list_with_counts(self):
        url = reverse("countries_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertTrue(
            any("airport_count" in c and "airline_count" in c for c in data)
        )

    def test_get_airlines_list_filters(self):
        url = reverse("airlines_list")
        resp = self.client.get(url, {"active": "Y"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertGreaterEqual(len(data), 1)
        self.assertTrue(
            all(a["active"].upper() == "Y" for a in data if a.get("active"))
        )

    def test_get_airports_missing_codes(self):
        url = reverse("airports_missing_codes")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertTrue(any(a.get("airport_id") == 1002 for a in data))

    def test_get_city_airport_counts_for_country(self):
        url = reverse("country_city_airport_counts", kwargs={"country_id": 274})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        # Expect Bangkok count >= 2
        bangkok = next((x for x in data if x["city"] == "Bangkok"), None)
        self.assertIsNotNone(bangkok)
        self.assertGreaterEqual(bangkok["airport_count"], 2)

    def test_post_create_airport_success(self):
        url = reverse("airport_create")
        payload = {
            "airport_id": 999001,
            "name": "Unit Test Airport",
            "city": "Unit City",
            "country_id": 112,
            "iata": "ZZZ",
            "icao": "ZZZZ",
            "latitude": 1.234567,
            "longitude": 103.123456,
            "altitude_ft": 10,
            "timezone_hrs": 8,
            "dst": "N",
            "tz": "Asia/Singapore",
            "type": "airport",
            "source": "tests",
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json()["airport_id"], 999001)
        self.assertEqual(resp.json()["iata"], "ZZZ")

    def test_post_create_airport_invalid_iata(self):
        url = reverse("airport_create")
        payload = {
            "airport_id": 999002,
            "name": "Bad IATA Airport",
            "city": "Bad City",
            "country_id": 112,
            "iata": "TOO-LONG",  # invalid
            "icao": "BADC",
            "type": "airport",
            "source": "tests",
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("iata", resp.json())

    def test_patch_update_airport_city(self):
        url = reverse("airport_detail", kwargs={"airport_id": 1001})
        resp = self.client.patch(url, {"city": "New City"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["city"], "New City")

    def test_delete_airport(self):
        url = reverse("airport_detail", kwargs={"airport_id": 1004})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_airport_form_page_loads(self):
        resp = self.client.get("/airport-form/")
        self.assertEqual(resp.status_code, 200)