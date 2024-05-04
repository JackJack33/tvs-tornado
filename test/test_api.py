import argparse
import os
import requests
import logging
import datetime
from random import randint
from time import sleep


def test_data_route(ip='localhost'):
    '''
    Function to test the data route's ability to delete, recreate, and access the database
    '''
    logging.info('Testing DELETE /data...')
    res = requests.delete(f'http://{ip}:5000/data')
    assert res.status_code == 200
    assert res.text == 'Successfully deleted data from database.\n'

    logging.info('Testing GET /data [no data in server]...')
    res = requests.get(f'http://{ip}:5000/data')
    assert res.status_code == 200

    logging.info('Testing POST /data...')
    res = requests.post(f'http://{ip}:5000/data')
    assert res.status_code == 200
    assert res.text in ['Successfully created database.\n', 'Data already loaded.\n']

    logging.info('Testing GET /data...')
    res = requests.get(f'http://{ip}:5000/data')
    assert isinstance(data := res.json(), list) and data and len(data) > 0


def test_jobs_and_results_route(ip='localhost'):
    '''
    Function to test the jobs and results route's ability to create jobs, get realtime updates, and retrieve results
    '''
    res = requests.post(f'http://{ip}:5000/data')
    assert res.status_code == 200
    start = datetime.date(randint(2006, 2016), randint(1, 12), randint(1, 28))
    end = start + 2 * datetime.timedelta(days=365)

    logging.info(f'Testing POST /jobs [with start ({start.strftime("%Y-%m-%d")}) and end ({end.strftime("%Y-%m-%d")})]...')
    res = requests.post(f'http://{ip}:5000/jobs',
                        json={'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d'),
                              'warning_types': ['TORNADO', 'FLASH FLOOD'], 'polygon': 'POLYGON((30.26153685272767 -97.79205322265626 30.26153685272767 -97.79205322265626 30.238700652972533 -97.66639709472658 30.238700652972533 -97.66639709472658 30.308082522961225 -97.65850067138672 30.308082522961225 -97.65850067138672 30.33831054738433 -97.80338287353517 30.33831054738433 -97.80338287353517))'})
    assert res.status_code == 200
    assert isinstance(data := res.json(), dict) and data['status'] in ['Submitted', 'In Progress']

    logging.info(f'Testing GET /jobs/<jid> [with jid ({data["id"]})]...')
    sleep(1)
    res = requests.get(f'http://{ip}:5000/jobs/{data["id"]}')
    assert res.status_code == 200
    assert isinstance(data := res.json(), dict) and data['status'] == 'In Progress'

    logging.info(f'Testing GET /results/<jid> [while job in progress with jid ({data["id"]})]...')
    res = requests.get(f'http://{ip}:5000/results/{data["id"]}')
    assert res.status_code == 200 and res.text == 'Job is in progress.\n'

    logging.info('Testing GET /results/<jid> [with an invalid jid]...')
    res = requests.get(f'http://{ip}:5000/results/fake_jid')
    assert res.status_code == 200 and res.text == 'Error: No information found for the given job ID.\n'

    logging.info('Querying GET /jobs/<jid> until job is complete...')
    while requests.get(f'http://{ip}:5000/jobs/{data["id"]}').json()['status'] != 'Complete':
        sleep(3)

    logging.info(f'Testing GET /results/<jid> [with jid ({data["id"]})]...')
    res = requests.get(f'http://{ip}:5000/results/{data["id"]}')
    assert res.status_code == 200
    assert isinstance(data := res.json(), list) and len(data) > 0

    logging.info('Testing GET /jobs...')
    res = requests.get(f'http://{ip}:5000/jobs')
    assert res.status_code == 200 and isinstance(data := res.json(), list) and len(data) > 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Route Testing')
    parser.add_argument('ip', type=str, help='IP address of REST API')
    args = vars(parser.parse_args())
    ip = args.get('ip', 'localhost')
    os.environ['REDIS_IP'] = ip

    test_data_route(ip)
    test_jobs_and_results_route(ip)

    logging.info('Test successfully completed')
