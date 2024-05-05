import logging
from io import BytesIO
import base64
import redis.exceptions
from matplotlib.figure import Figure
from redis_handler import RedisHandler, RedisEnum
from shapely.geometry import Polygon
from pyproj import Transformer
from datetime import datetime
import pandas as pd
from itertools import repeat

handler = RedisHandler()
q = handler._get_q_obj()
transformer_to_cartesian = Transformer.from_crs(4326, 5070)
transformer_to_geographic = Transformer.from_crs(5070, 4326)


def to_cartesian(lon, lat):
    return transformer_to_cartesian.transform(lat, lon) # Switched for some reason


def to_geographic(x, y):
    return transformer_to_geographic.transform(x, y)


def convert_to_polygon(poly_string_in):
    coords_str = poly_string_in.split("(")[-1].split(")")[0] # POLYGON((Lon Lat Lon Lat...))
    coords = coords_str.strip().split()
    lon_lat_pairs = [(float(coords[i]), float(coords[i+1])) for i in range(0, len(coords), 2)]
    lon_lat_pairs_cartesian = [to_cartesian(lon, lat) for lon, lat in lon_lat_pairs]
    return Polygon(lon_lat_pairs_cartesian)


def do_polygons_intersect(poly1_in, poly2_in): # Separated for testing purposes
    return poly1_in.intersects(poly2_in)


def count_relevant_polygon_intersections(warning_types, start_timestamp, end_timestamp, interest_poly_string, data_dict):

    # Initialize counts dictionary, months, warning_types
    months = []
    counts = {}

    for year in range(start_timestamp.year, end_timestamp.year + 1):
        counts[year] = {}
        for month in range(1, 12+1):
            counts[year][month] = {}
            months.append([str(month), str(year)])
            for warning_type in warning_types:
                counts[year][month][warning_type] = 0


    # Filter relevant warnings
    interest_poly = convert_to_polygon(interest_poly_string)
    for val in data_dict:
        val_timestamp = datetime.strptime(val['#ISSUEDATE'], '%Y-%m-%d %H:%M:%S.%f')


        if (val_timestamp < start_timestamp) or (val_timestamp > end_timestamp):
            continue

        warning_poly = convert_to_polygon(val['POLYGON'])

        if not (do_polygons_intersect(interest_poly, warning_poly)):
            continue

        year = val_timestamp.year
        month = val_timestamp.month
        counts[year][month][val['WARNINGTYPE']] += 1

    return counts, months


@q.worker
def worker(job_info):

    # Needs inputs:
    # - start_date : start timestamp string
    # - end_date   : end timestamp string
    # - polygon    : polygon string of interest

    logging.info("Worker function started.")

    warning_types = job_info['warning_types'].split(', ')
    start_date = datetime.strptime(job_info['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(job_info['end_date'], '%Y-%m-%d')

    logging.info(warning_types)
    handler.set(RedisEnum.JOBS, job_info['id'], ('status', 'In Progress'))

    logging.info("Retrieving all Redis data...")
    data_dict = handler.get_all_data()

    logging.info("Done. Counting...")
    counts, months = count_relevant_polygon_intersections(warning_types, start_date, end_date, job_info['polygon'], data_dict)

    logging.info("Done. Graphing...")

    # Graph
    fig = Figure()
    ax = fig.subplots()

    def get_count(dates, warning_type):
        logging.info("--------")
        logging.info(dates)
        logging.info(warning_type)
        logging.info(dates[1])
        logging.info(dates[0])
        logging.info(counts[dates[1]])
        logging.info(counts[dates[1]][dates[0]])
        logging.info(counts[dates[1]][dates[0]][warning_type])
        logging.info("--------")
        try:
            return counts[dates[1]][dates[0]][warning_type]
        except KeyError:
            return 0

    flattened_months = [f"{month}-{year}" for month, year in months]

    logging.info("=========================")
    logging.info(counts)
    logging.info("=========================")
    logging.info(months)
    logging.info("=========================")
    logging.info(flattened_months)
    logging.info("=========================")

    for warning_type in warning_types:
        counts_list = [get_count([int(month), int(year)], warning_type) for month, year in months]
        ax.plot(flattened_months, counts_list, label=warning_type)
        logging.info(counts_list)
        logging.info("-=-=-=-=-=-=-=-=-=-=-=-=-")

    ax.set_xlabel('Time')
    ax.set_ylabel('Count')
    ax.set_title('Event Counts Over Time')
    ax.legend()
    ax.grid(True)
    ax.tick_params(axis='x', rotation=45)


    logging.info("Done. Exporting...")

    # Completion

    buf = BytesIO()
    fig.savefig(buf, format='png')
    handler.set(RedisEnum.RESULTS, job_info['id'], base64.b64encode(buf.getbuffer()))
    handler.set(RedisEnum.JOBS, job_info['id'], ('status', 'Complete'))
    logging.info("Done. Worker function ended.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        worker()
    except redis.exceptions.BusyLoadingError:
        from time import sleep
        sleep(5)
        worker()
