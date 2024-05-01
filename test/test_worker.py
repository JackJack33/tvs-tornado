import pytest
from pygeodesy.sphericalNvector import LatLon
from shapely.geometry import Polygon
from shapely.ops import transform
from pyproj import Transformer
from datetime import datetime

import worker

def test_to_cartesian():
    lon, lat = -122.4194, 37.7749 # San Francisco
    expected_x, expected_y = -2275431.8571, 1955935.27187

    x, y = to_cartesian(lon, lat)
    assert round(x, 2) == round(expected_x, 2)
    assert round(y, 2) == round(expected_y, 2)


def test_to_geographic():
    x, y = -2275431.8571, 1955935.27187 # San Francisco
    expected_lon, expected_lat = -122.4194, 37.7749

    lon, lat = to_geographic(x, y)
    assert round(lon, 2) == round(expected_lon, 2)
    assert round(lat, 2) == round(expected_lat, 2)


def test_convertToPolygon():
    poly_string_in = "POLYGON((-122.4183 37.7753 -122.4184 37.7750 -122.4181 37.7749 -122.4178 37.7752 -122.4183 37.7753))"
    polygon = convertToPolygon(poly_string_in)
    assert isinstance(polygon, Polygon)

def test_doPolygonsIntersect():
    poly1_in = "POLYGON((-122.4183 37.7753 -122.4184 37.7750 -122.4181 37.7749 -122.4178 37.7752 -122.4183 37.7753))"
    poly2_in = "POLYGON((-122.4190 37.7747 -122.4187 37.7744 -122.4184 37.7747 -122.4187 37.7750 -122.4190 37.7747))"
    assert test_doPolygonsIntersect(poly1_in, poly2_in) == True

def test_countRelevantPolygonIntersections():
    start_timestamp = datetime(2024, 1, 1)
    end_timestamp = datetime(2024, 12, 31)
    interest_poly_string = "POLYGON((-122.42 37.775, -122.419 37.774, -122.418 37.775, -122.419 37.776, -122.42 37.775))"
    data_dict = [
        {'timestamp': '2024-01-05 10:00:00', 'type': 'SEVERE THUNDERSTORM', 'polygon': 'POLYGON((-122.41 37.776, -122.409 37.775, -122.41 37.774, -122.411 37.775, -122.41 37.776))'},
        {'timestamp': '2024-02-10 12:00:00', 'type': 'TORNADO', 'polygon': 'POLYGON((-122.415 37.778, -122.414 37.777, -122.413 37.778, -122.414 37.779, -122.415 37.778))'},
        {'timestamp': '2024-03-15 15:00:00', 'type': 'FLASH FLOOD', 'polygon': 'POLYGON((-122.418 37.777, -122.417 37.776, -122.416 37.777, -122.417 37.778, -122.418 37.777))'},
        {'timestamp': '2024-04-20 18:00:00', 'type': 'SPECIAL MARINE', 'polygon': 'POLYGON((-122.419 37.778, -122.418 37.777, -122.417 37.778, -122.418 37.779, -122.419 37.778))'}
    ]

    counts = countRelevantPolygonIntersections(start_timestamp, end_timestamp, interest_poly_string, data_dict)

    assert isinstance(counts, dict)
    for year in range(start_timestamp.year, end_timestamp.year + 1):
        assert year in counts
        for month in range(1, 12+1):
            assert month in counts[year]
            for warning_type in ['SEVERE THUNDERSTORM', 'TORNADO', 'FLASH FLOOD', 'SPECIAL MARINE']:
                assert warning_type in counts[year][month]
                assert isinstance(counts[year][month][warning_type], int)
