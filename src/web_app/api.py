from flask import Flask, request, render_template
import logging
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parent.parent))
import os
if 'SCRIPT' in os.environ:
    from redis_handler import RedisHandler, RedisEnum
else:
    from src.redis_handler import RedisHandler

app = Flask(__name__)
handler = RedisHandler()


@app.route('/', methods=['GET'])
def index():
    """
    Main Route which only works when data exists on the server, otherwise returns an error message.

    :return:        HTML        web app webpage
    """
    if len(handler.get_keys(RedisEnum.DATA)) == 0:
        return 'Error: No data has been POSTed to the server. The webpage will remain inactive until such a time.\n'

    return render_template('index.html', host_ip=os.environ['REDIS_IP'])


@app.route('/help', methods=['GET'])
def get_help():
    """
    Route to return help information

    :return:        str          help information
    """
    with open('static/help.txt', 'r') as f:
        return list(f)


@app.route('/data', methods=['GET', 'POST', 'DELETE'])
def data():
    """
    Route to pull data into, retrieve data from, or delete data from Redis database.

    Return by method:
        GET     JSON    Return JSON representation of all records from Redis database
        POST    str     Pull data from NOAA static host and add it to Redis database, return success message
        DELETE  str     Delete data from Redis database
    """
    if request.method == 'POST':
        logging.info('Retrieving data from NOAA data host...')
        try:
            [handler.post_tvs_data(f'https://www.ncei.noaa.gov/pub/data/swdi/database-csv/v2/warn-20{year:02}.csv.gz') for year in range(6, 17)]
            return 'Successfully created database.\n'
        except EnvironmentError:
            logging.warning('POST /data request made with data already in Redis database...')
            return 'Data already loaded.\n'
    elif request.method == 'GET':
        logging.info('Returning NOAA dataset from Redis database...')
        try:
            return handler.get_all_data()
        except EnvironmentError:
            logging.warning('GET /data request made with no data in database...')
            return 'Error: No data available. Try using POST /data route first.\n'
    elif request.method == 'DELETE':
        logging.info('Deleting data from Redis database...')
        handler.delete_db(RedisEnum.DATA)
        return 'Successfully deleted data from database.\n'
    return 'Error: Invalid request method.\n'


@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    """
    Route to get list of existing jobs by IDs or create a job

    Return by method:
        GET     list    Return list of all job IDs in jobs database
        POST    str     Creates new job from web app inputs and returns ID of created job
    """
    if request.method == 'POST':
        request.json['polygon'] = 'POLYGON((' + ' '.join([f'{lon} {lat}' for lon, lat in request.json['polygon']]) + '))'
        request.json['warning_types'] = ', '.join(request.json['warning_types'])
        jid = handler.add_job(request.json)
        logging.info(f'Job {jid} added to Redis database...')
        return {key.decode(): val.decode() for key, val in handler.get(RedisEnum.JOBS, jid, True).items()}
    elif request.method == 'GET':
        return handler.get_keys(RedisEnum.JOBS)


@app.route('/jobs/<jid>', methods=['GET'])
def job_info(jid):
    '''
    Route to return information about a given job ID from Redis database

    :param jid:    str      Job ID
    :return:       JSON     Job information
    '''
    return {key.decode(): val.decode() for key, val in handler.get(RedisEnum.JOBS, jid, True).items()}


@app.route('/results/<jid>', methods=['GET'])
def results(jid):
    """
    Route to return base64 encoded png results from a given job ID from Redis database

    :param jid:
    :return:        bytes       base64 encoded png result
    """
    logging.info(f'Request made to get results for jid: {jid}...')
    status = handler.hget(RedisEnum.JOBS, jid, 'status').decode()
    if status in ['In Progress', 'Submitted']:
        return 'Job is in progress.\n'
    elif status == 'Complete':
        return handler.get(RedisEnum.RESULTS, jid).decode()
    else:
        return 'Error: Job ID does not exist in database.\n'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run('0.0.0.0', port=5000)