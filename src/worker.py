import os
from io import BytesIO
import base64
import matplotlib.pyplot as plt
from hotqueue import HotQueue
from redis_handler import RedisHandler, RedisEnum
from pygeodesy.sphericalNvector import LatLon
from shapely.geometry import Polygon
from shapely.ops import transform
from pyproj import Transformer
from datetime import datetime

q = HotQueue('queue', host=os.environ['REDIS_IP'], port=6379, db=3)
handler = RedisHandler()

def to_cartesian(lon, lat):
    transformer = Transformer.from_crs(4326, 5070)  # EPSG:4326 (WGS 84) to EPSG:5070 (NAD83 / Conus Albers)
    return transformer.transform(lon, lat)

def to_geographic(x, y):
    transformer = Transformer.from_crs(5070, 4326)  # EPSG:5070 (NAD83 / Conus Albers) to EPSG:4326 (WGS 84)
    return transformer.transform(x, y)

def convertToPolygon(poly_string_in):
    coords_str = poly_string_in.split("((")[1].split("))")[0] # POLYGON((Lon Lat Lon Lat...))
    coords = coords_str.strip().split()
    lon_lat_pairs = [(float(coords[i]), float(coords[i+1])) for i in range(0, len(coords), 2)]
    lon_lat_pairs_cartesian = [to_cartesian(lon, lat) for lon, lat in lon_lat_pairs]
    return Polygon(lon_lat_pairs_cartesian)

def doPolygonsIntersect(poly1_in, poly2_in):
    poly1 = convertToPolygon(poly1_in)
    poly2 = convertToPolygon(poly2_in)
    return poly1.intersects(poly2)

def countRelevantPolygonIntersections(start_timestamp, end_timestamp, interest_poly_string, data_dict):

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
    interest_poly = convertToPolygon(interest_poly_string)
    for val in data_dict:
        val_timestamp = datetime.strptime(val['timestamp'], "%Y-%m-%d %H:%M:%S")
        if (val_timestamp < start_timestamp) or (val_timestamp > end_timestamp):
            continue
        warning_poly = convertToPolygon(val['polygon'])
        if not (doPolygonsIntersect(interest_poly, warning_poly)):
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

    # change formats to whatever works for html :)
    start_timestamp = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    end_timestamp = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")

    handler.set(RedisEnum.JOBS, job_info['id'], ('status', 'In Progress'))
    data_dict = handler.get_all_data()
    counts = countRelevantPolygonIntersections(start_timestamp, end_timestamp, interest_poly_string, data_dict)

    # Graph

    fig = plt.figure()
    for warning_type in warning_types:
        counts_list = [counts[(year, month)][warning_type] for year, month in zip(months)]
        plt.plot(months, counts_list, label=warning_type)
    plt.xlabel('Time')
    plt.ylabel('Count')
    plt.title('Event Counts Over Time')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)

    # Completion

    buf = BytesIO()
    fig.savefig(buf, format='png')
    handler.set(RedisEnum.RESULTS, job_info['id'], base64.b64encode(buf.getbuffer()))
    handler.set(RedisEnum.JOBS, job_info['id'], ('status', 'Complete'))



if __name__ == '__main__':
    worker()
