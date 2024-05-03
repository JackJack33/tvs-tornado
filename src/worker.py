from io import BytesIO
import base64
from matplotlib.figure import Figure
from redis_handler import RedisHandler, RedisEnum
from shapely.geometry import Polygon
from pyproj import Transformer
from datetime import datetime
import pandas as pd
from itertools import repeat

handler = RedisHandler()
q = handler._get_q_obj()


def to_cartesian(lon, lat):
    transformer = Transformer.from_crs(4326, 5070)  # EPSG:4326 (WGS 84) to EPSG:5070 (NAD83 / Conus Albers)
    return transformer.transform(lon, lat)


def to_geographic(x, y):
    transformer = Transformer.from_crs(5070, 4326)  # EPSG:5070 (NAD83 / Conus Albers) to EPSG:4326 (WGS 84)
    return transformer.transform(x, y)


def convert_to_polygon(poly_string_in):
    coords_str = poly_string_in.split("((")[1].split("))")[0] # POLYGON((Lon Lat Lon Lat...))
    coords = coords_str.strip().split()
    lon_lat_pairs = [(float(coords[i]), float(coords[i+1])) for i in range(0, len(coords), 2)]
    lon_lat_pairs_cartesian = [to_cartesian(lon, lat) for lon, lat in lon_lat_pairs]
    return Polygon(lon_lat_pairs_cartesian)


def do_polygons_intersect(poly1_in, poly2_in):
    poly1 = convert_to_polygon(poly1_in)
    poly2 = convert_to_polygon(poly2_in)
    return poly1.intersects(poly2)


def count_relevant_polygon_intersections(start_timestamp, end_timestamp, interest_poly_string, data_dict):

    # Initialize counts dictionary, months, warning_types
    warning_types = ['SEVERE THUNDERSTORM', 'TORNADO', 'FLASH FLOOD', 'SPECIAL MARINE']
    months = []
    counts = {}
    for year in range(start_timestamp.year, end_timestamp.year + 1):
        for month in range(1, 12+1):
            months.append(datetime(year, month, 1))
            for warning_type in warning_types:
                counts[year][month][warning_type] = 0

    # Filter relevant warnings
    interest_poly = convert_to_polygon(interest_poly_string)
    for val in data_dict:
        val_timestamp = datetime.strptime(val['timestamp'], '%Y-%m-%d %H:%M:%S')
        if (val_timestamp < start_timestamp) or (val_timestamp > end_timestamp):
            continue
        warning_poly = convert_to_polygon(val['polygon'])
        if not (do_polygons_intersect(interest_poly, warning_poly)):
            continue

        year = val_timestamp.year
        month = val_timestamp.month
        counts[year][month][val['type']] += 1

    return counts


@q.worker
def worker(job_info):

    # Need inputs:
    # - start                  : start timestamp string
    # - end                    : end timestamp string
    # - interest_poly_string   : polygon string of interest

    start_date = datetime.strptime(job_info['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(job_info['end_date'], '%Y-%m-%d')

    handler.set(RedisEnum.JOBS, job_info['id'], ('status', 'In Progress'))
    data_dict = handler.get_all_data()
    counts = count_relevant_polygon_intersections(start_date, end_date, job_info['polygon'], data_dict)

    # Graph
    fig = Figure()
    ax = fig.subplots()
    months = pd.date_range('2006-1-1','2016-12-31', freq='1ME').strftime('%m-%Y').str.split('-').tolist()

    def get_count(dates, warning_type):
        try:
            return counts[dates[1]][dates[0]][warning_type]
        except KeyError:
            return 0

    for warning_type in job_info['warning_types']:
        counts_list = list(map(get_count, months, repeat(warning_type)))
        ax.plot(months, counts_list, label=warning_type)
    ax.xlabel('Time')
    ax.ylabel('Count')
    ax.title('Event Counts Over Time')
    ax.legend()
    ax.grid(True)
    ax.xticks(rotation=45)

    # Completion

    buf = BytesIO()
    fig.savefig(buf, format='png')
    handler.set(RedisEnum.RESULTS, job_info['id'], base64.b64encode(buf.getbuffer()))
    handler.set(RedisEnum.JOBS, job_info['id'], ('status', 'Complete'))


if __name__ == '__main__':
    worker()
