import pytest
from shapely.geometry import Polygon
from pyproj import Transformer
from datetime import datetime

from worker import to_cartesian, to_geographic, convert_to_polygon, do_polygons_intersect, count_relevant_polygon_intersections

def test_to_cartesian():
    lon, lat = -122.4194, 37.7749 # San Francisco
    expected_x, expected_y = -2275431.8571, 1955935.27187

    x, y = to_cartesian(lon, lat)
    assert round(x) == round(expected_x)
    assert round(y) == round(expected_y)


def test_to_geographic():
    x, y = -2275431.8571, 1955935.27187 # San Francisco
    expected_lon, expected_lat = -122.4194, 37.7749

    lat, lon = to_geographic(x, y)
    assert round(lon) == round(expected_lon)
    assert round(lat) == round(expected_lat)


def test_convert_to_polygon():
    poly_string_in = "POLYGON((-96.8 32.8 -90.1 35.1 -96 36.2))" # Dallas, TX -> Memphis, TN -> Tulsa, OK
    polygon = convert_to_polygon(poly_string_in)
    assert isinstance(polygon, Polygon)

def test_do_polygons_intersect():
    poly1_str = "POLYGON((-100.4 31.5 -98.5 29.4 -97.2 31.6))" # San Angelo, TX -> San Antonio, TX -> Waco, TX
    poly2_str = "POLYGON((-99.7 32.4 -99.8 29.2 -96.4 30.7))" # Abilene, TX -> Uvalde, TX -> Bryan, TX
    poly1_in = convert_to_polygon(poly1_str)
    poly2_in = convert_to_polygon(poly2_str)
    assert do_polygons_intersect(poly1_in, poly2_in) == True

def test_count_relevant_polygon_intersections():

    warning_types = ['SEVERE THUNDERSTORM', 'TORNADO', 'FLASH FLOOD', 'SPECIAL MARINE']
    start_timestamp = datetime(2024, 1, 1)
    end_timestamp = datetime(2024, 12, 31)
    interest_poly_string = "POLYGON((-100.4 31.5 -98.5 29.4 -97.2 31.6))" # San Angelo, TX -> San Antonio, TX -> Waco, TX
    data_dict = [
        # Abilene, TX -> Uvalde, TX -> Bryan, TX
        {'#ISSUEDATE': '2024-01-05 10:00:00.0', 'WARNINGTYPE': 'SEVERE THUNDERSTORM', 'POLYGON': 'POLYGON((-99.7 32.4 -99.8 29.2 -96.4 30.7))'},
        {'#ISSUEDATE': '2024-02-10 12:00:00.0', 'WARNINGTYPE': 'TORNADO', 'POLYGON': 'POLYGON((-99.7 32.4 -99.8 29.2 -96.4 30.7))'},
        {'#ISSUEDATE': '2024-03-15 15:00:00.0', 'WARNINGTYPE': 'FLASH FLOOD', 'POLYGON': 'POLYGON((-99.7 32.4 -99.8 29.2 -96.4 30.7))'},
        {'#ISSUEDATE': '2024-04-20 18:00:00.0', 'WARNINGTYPE': 'SPECIAL MARINE', 'POLYGON': 'POLYGON((-99.7 32.4 -99.8 29.2 -96.4 30.7))'}
    ]

    counts, months = count_relevant_polygon_intersections(warning_types, start_timestamp, end_timestamp, interest_poly_string, data_dict)

    print(counts)
    print(months)

    assert isinstance(counts, dict)
    assert isinstance(months, list)

    for year in range(start_timestamp.year, end_timestamp.year + 1):
        assert year in counts
        for month in range(1, 12+1):
            assert month in counts[year]
            for warning_type in ['SEVERE THUNDERSTORM', 'TORNADO', 'FLASH FLOOD', 'SPECIAL MARINE']:
                assert warning_type in counts[year][month]
                assert isinstance(counts[year][month][warning_type], int)


if __name__ == '__main__':
    test_to_cartesian()
    test_to_geographic()
    test_convert_to_polygon()
    test_do_polygons_intersect()
    test_count_relevant_polygon_intersections()
