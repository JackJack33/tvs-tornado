import os
from io import BytesIO
import base64
from hotqueue import HotQueue
from redis_handler import RedisHandler, RedisEnum
from matplotlib.figure import Figure

q = HotQueue('queue', host=os.environ['REDIS_IP'], port=6379, db=3)
handler = RedisHandler()


@q.worker
def worker(job_info):
    handler.set(RedisEnum.JOBS, job_info['id'], ('status', 'In Progress'))
    fig = Figure()
    ax = fig.subplots()
    ax.plot(x := list(range(10)), [elem ** 2 for elem in x])
    buf = BytesIO()
    fig.savefig(buf, format='png')
    handler.set(RedisEnum.RESULTS, job_info['id'], base64.b64encode(buf.getbuffer()))
    handler.set(RedisEnum.JOBS, job_info['id'], ('status', 'Complete'))


if __name__ == '__main__':
    worker()
