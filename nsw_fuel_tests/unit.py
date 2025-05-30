import datetime
import json
import os
import unittest

from requests_mock import Mocker

from nsw_fuel import FuelCheckClient, Period, FuelCheckError
from nsw_fuel.client import API_URL_BASE


class FuelCheckClientTest(unittest.TestCase):
    def test_construction(self) -> None:
        FuelCheckClient()

    @Mocker()
    def test_get_fuel_prices(self, m: Mocker) -> None:
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures/all_prices.json')
        with open(fixture_path) as fixture:
            m.get(
                '{}/prices'.format(API_URL_BASE),
                json=json.load(fixture)
            )
            client = FuelCheckClient()
            response = client.get_fuel_prices()

            self.assertEqual(len(response.stations), 2)
            self.assertEqual(len(response.prices), 5)
            self.assertEqual(response.stations[0].name, 'Cool Fuel Brand Hurstville')
            self.assertEqual(response.stations[1].name, 'Fake Fuel Brand Kogarah')
            self.assertAlmostEqual(response.stations[1].latitude, -31)
            self.assertAlmostEqual(response.stations[1].longitude, 152)
            self.assertEqual(response.prices[0].fuel_type, 'DL')
            self.assertEqual(response.prices[1].fuel_type, 'E10')
            self.assertEqual(response.prices[1].station_code, 1)
            self.assertEqual(response.prices[3].fuel_type, 'P95')
            self.assertEqual(response.prices[3].station_code, 2)

    @Mocker()
    def test_get_fuel_prices_server_error(self, m: Mocker) -> None:
        m.get(
            '{}/prices'.format(API_URL_BASE),
            status_code=500,
            text='Internal Server Error.',
        )

        client = FuelCheckClient()
        with self.assertRaises(FuelCheckError) as cm:
            client.get_fuel_prices()

        self.assertEqual(str(cm.exception), 'Internal Server Error.')

    @Mocker()
    def test_get_fuel_prices_for_station(self, m: Mocker) -> None:
        m.get('{}/prices/station/100'.format(API_URL_BASE), json={
            'prices': [
                {
                    'fueltype': 'E10',
                    'price': 146.9,
                    'lastupdated': '02/06/2018 02:03:04',
                },
                {
                    'fueltype': 'P95',
                    'price': 150.0,
                    'lastupdated': '02/06/2018 02:03:04',
                }
            ]
        })
        client = FuelCheckClient()
        result = client.get_fuel_prices_for_station(100)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].fuel_type, 'E10')
        self.assertEqual(result[0].price, 146.9)
        self.assertEqual(result[0].last_updated, datetime.datetime(
            day=2,
            month=6,
            year=2018,
            hour=2,
            minute=3,
            second=4,
        ))

    @Mocker()
    def test_get_fuel_prices_within_radius(self, m: Mocker) -> None:
        m.post('{}/prices/nearby'.format(API_URL_BASE), json={
            'stations': [
                {
                    'stationid': 'SAAAAAA',
                    'brandid': 'BAAAAAA',
                    'brand': 'Cool Fuel Brand',
                    'code': 678,
                    'name': 'Cool Fuel Brand Luxembourg',
                    'address': '123 Fake Street',
                    'location': {'latitude': -33.987, 'longitude': 151.334},
                },
                {
                    'stationid': 'SAAAAAB',
                    'brandid': 'BAAAAAB',
                    'brand': 'Fake Fuel Brand',
                    'code': 679,
                    'name': 'Fake Fuel Brand Luxembourg',
                    'address': '123 Fake Street',
                    'location': {'latitude': -33.587, 'longitude': 151.434},
                },
                {
                    'stationid': 'SAAAAAB',
                    'brandid': 'BAAAAAB',
                    'brand': 'Fake Fuel Brand2',
                    'code': 880,
                    'name': 'Fake Fuel Brand2 Luxembourg',
                    'address': '123 Fake Street',
                    'location': {'latitude': -33.687, 'longitude': 151.234},
                },
            ],
            'prices': [
                {
                    'stationcode': 678,
                    'fueltype': 'P95',
                    'price': 150.9,
                    'priceunit': 'litre',
                    'description': None,
                    'lastupdated': '2018-06-02 00:46:31'
                },
                {
                    'stationcode': 678,
                    'fueltype': 'P95',
                    'price': 130.9,
                    'priceunit': 'litre',
                    'description': None,
                    'lastupdated': '2018-06-02 00:46:31'
                },
                {
                    'stationcode': 880,
                    'fueltype': 'P95',
                    'price': 155.9,
                    'priceunit': 'litre',
                    'description': None,
                    'lastupdated': '2018-06-02 00:46:31'
                }
            ],
        })

        client = FuelCheckClient()
        result = client.get_fuel_prices_within_radius(
            longitude=151.0,
            latitude=-33.0,
            radius=10,
            fuel_type='E10',
        )
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].station.code, 678)
        self.assertAlmostEqual(result[0].station.latitude, -33.987)
        self.assertAlmostEqual(result[0].station.longitude, 151.334)
        self.assertEqual(result[0].price.price, 150.9)

    @Mocker()
    def test_get_fuel_price_trends(self, m: Mocker) -> None:
        m.post('{}/prices/trends/'.format(API_URL_BASE), json={
            'Variances': [
                {'Code': 'E10', 'Period': 'Day', 'Price': 150.0},
                {'Code': 'E10', 'Period': 'Week', 'Price': 151.0},
                {'Code': 'E10', 'Period': 'Month', 'Price': 152.0},
                {'Code': 'E10', 'Period': 'Year', 'Price': 153.0},
                {'Code': 'P95', 'Period': 'Day', 'Price': 150.0},
                {'Code': 'P95', 'Period': 'Week', 'Price': 151.0},
                {'Code': 'P95', 'Period': 'Month', 'Price': 152.0},
                {'Code': 'P95', 'Period': 'Year', 'Price': 153.0},
            ],
            'AveragePrices': [
                {'Code': 'E10', 'Period': 'Day', 'Price': 150.0,
                 'Captured': '2018-06-02'},
                {'Code': 'E10', 'Period': 'Year', 'Price': 151.0,
                 'Captured': 'October 2017'}
            ],
        })

        client = FuelCheckClient()
        result = client.get_fuel_price_trends(
            longitude=151.0,
            latitude=-33.0,
            fuel_types=['E10', 'P95']
        )

        self.assertEqual(len(result.variances), 8)
        self.assertEqual(result.variances[0].price, 150.0)
        self.assertEqual(result.variances[0].period, Period.DAY)
        self.assertEqual(result.variances[0].fuel_type, 'E10')

        self.assertEqual(len(result.average_prices), 2)
        self.assertEqual(result.average_prices[0].fuel_type, 'E10')
        self.assertEqual(result.average_prices[0].period, Period.DAY)
        self.assertEqual(result.average_prices[0].captured,
                         datetime.datetime(year=2018, month=6, day=2))
        self.assertEqual(result.average_prices[0].price, 150.0)

        self.assertEqual(result.average_prices[1].period, Period.YEAR)
        self.assertEqual(result.average_prices[1].captured,
                         datetime.datetime(year=2017, month=10, day=1))

    @Mocker()
    def test_get_fuel_prices_for_station_client_error(self, m: Mocker) -> None:
        m.get(
            '{}/prices/station/21199'.format(API_URL_BASE),
            status_code=400,
            json={
                "errorDetails": [
                    {
                        "code": "E0014",
                        "description": "Invalid service station code \"21199\""
                    }
                ]
            }
        )
        client = FuelCheckClient()
        with self.assertRaises(FuelCheckError) as cm:
            client.get_fuel_prices_for_station(21199)

        self.assertEqual(str(cm.exception), 'Invalid service station code "21199"')

    @Mocker()
    def test_get_fuel_prices_for_station_server_error(self, m: Mocker) -> None:
        m.get(
            '{}/prices/station/21199'.format(API_URL_BASE),
            status_code=500,
            text='Internal Server Error.',
        )
        client = FuelCheckClient()
        with self.assertRaises(FuelCheckError) as cm:
            client.get_fuel_prices_for_station(21199)

        self.assertEqual(str(cm.exception), 'Internal Server Error.')

    @Mocker()
    def test_get_fuel_prices_within_radius_server_error(self, m: Mocker) -> None:
        m.post(
            '{}/prices/nearby'.format(API_URL_BASE),
            status_code=500,
            text='Internal Server Error.',
        )
        client = FuelCheckClient()
        with self.assertRaises(FuelCheckError) as cm:
            client.get_fuel_prices_within_radius(
                longitude=151.0,
                latitude=-33.0,
                radius=10,
                fuel_type='E10',
            )

        self.assertEqual(str(cm.exception), 'Internal Server Error.')

    @Mocker()
    def test_get_fuel_price_trends_server_error(self, m: Mocker) -> None:
        m.post(
            '{}/prices/trends/'.format(API_URL_BASE),
            status_code=500,
            text='Internal Server Error.',
        )
        client = FuelCheckClient()
        with self.assertRaises(FuelCheckError) as cm:
            client.get_fuel_price_trends(
                longitude=151.0,
                latitude=-33.0,
                fuel_types=['E10', 'P95']
            )

        self.assertEqual(str(cm.exception), 'Internal Server Error.')

    @Mocker()
    def test_get_reference_data(self, m: Mocker) -> None:
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures/lovs.json')
        with open(fixture_path) as fixture:
            m.get(
                '{}/lovs'.format(API_URL_BASE),
                json=json.load(fixture)
            )
            client = FuelCheckClient()
            response = client.get_reference_data()
            self.assertEqual(len(response.brands), 2)
            self.assertEqual(len(response.fuel_types), 2)
            self.assertEqual(len(response.stations), 2)
            self.assertEqual(len(response.trend_periods), 2)
            self.assertEqual(len(response.sort_fields), 2)
            self.assertEqual(response.brands[0], 'Cool Fuel Brand')
            self.assertEqual(response.fuel_types[0].code, 'E10')
            self.assertEqual(response.fuel_types[0].name, 'Ethanol 94')
            self.assertEqual(response.stations[0].name, 'Cool Fuel Brand Hurstville')
            self.assertEqual(response.trend_periods[0].period, 'Day')
            self.assertEqual(response.trend_periods[0].description, 'Description for day')
            self.assertEqual(response.sort_fields[0].code, 'Sort 1')
            self.assertEqual(response.sort_fields[0].name, 'Sort field 1')

    @Mocker()
    def test_get_reference_data_client_error(self, m: Mocker) -> None:
        m.get(
            '{}/lovs'.format(API_URL_BASE),
            status_code=400,
            json={
                "errorDetails": {
                    "code": "-2146233033",
                    "message": "String was not recognized as a valid DateTime."
                }
            })

        client = FuelCheckClient()
        with self.assertRaises(FuelCheckError) as cm:
            client.get_reference_data()

        self.assertEqual(
            str(cm.exception),
            'String was not recognized as a valid DateTime.'
        )

    @Mocker()
    def test_get_reference_data_server_error(self, m: Mocker) -> None:
        m.get(
            '{}/lovs'.format(API_URL_BASE),
            status_code=500,
            text='Internal Server Error.',
        )

        client = FuelCheckClient()
        with self.assertRaises(FuelCheckError) as cm:
            client.get_reference_data()

        self.assertEqual(str(cm.exception), 'Internal Server Error.')
