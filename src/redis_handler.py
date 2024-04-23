import os
import uuid
from typing import Union
import redis
import pandas as pd
from hotqueue import HotQueue


class RedisEnum:
    DATA = 0
    JOBS = 1
    RESULTS = 2
    QUEUE = 3


class RedisHandler:
    def __init__(self):
        # if 'REDIS_IP' not in os.environ:
        #     raise KeyError('REDIS_IP environment variable is not defined.')
        ip = os.getenv('REDIS_IP', 'localhost')
        self.db = [redis.Redis(host=ip, port=6379, db=num) for num in range(3)]
        self.q = HotQueue('queue', host=ip, port=6379, db=3)

    def get_all_data(self):
        keys = self.get_keys(RedisEnum.DATA)
        if len(keys) == 0:
            raise EnvironmentError('No data in Redis database.')
        return [{key.decode(): val.decode() for key, val in self.db[RedisEnum.DATA].hgetall(rd_key.decode()).items()} for rd_key in keys]

    def post_tvs_data(self, url: str):
        keys = self.get_keys(RedisEnum.DATA)
        if len(keys) != 0:
            raise EnvironmentError('Redis server already contains data.')

        pd.read_csv(url, header=2, compression='gzip').apply(lambda row: self.db[RedisEnum.DATA].hset(row.hgnc_id, mapping=dict(row)), axis=1)

    def get_keys(self, db_enum: int) -> list:
        return [val.decode() for val in self.db[db_enum].keys()]

    def delete_db(self, db_enum: int):
        for key in self.get_keys(db_enum):
            self.db[db_enum].delete(key)

    def set(self, db_enum: int, key, val: Union[dict, bytes, memoryview, str, int, float]):
        if isinstance(val, dict):
            self.db[db_enum].hset(key, mapping=val)
        elif isinstance(val, tuple) and len(val) == 2:
            self.db[db_enum].hset(key, *val)
        else:
            self.db[db_enum].set(key, val)

    def get(self, db_enum: int, key: str, is_dict: bool = False):
        return self.db[db_enum].hgetall(key) if is_dict else self.db[db_enum].get(key)

    def hget(self, db_enum: int, name: str, key: str):
        return self.db[db_enum].hget(name, key)

    def add_job(self):
        jid = str(uuid.uuid4())
        job_info = {'id': jid, 'status': 'Submitted'}
        self.db[RedisEnum.JOBS].hset(jid, mapping=job_info)
        self.add_to_q(job_info)
        return jid

    def add_to_q(self, obj):
        self.q.put(obj)


if __name__ == '__main__':
    handler = RedisHandler()
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    import matplotlib.image as mpimg
    import base64
    import io
    with io.BytesIO(base64.b64decode(handler.get(RedisEnum.RESULTS, '51d3225a-e5c3-46aa-ac0a-4c0cf9c33f2f').decode())) as fp:
        img = mpimg.imread(fp, format='png')
    plt.imshow(img)
    # fig = plt.figure()
    # ax = fig.subplots()
    # ax.plot(range(10), range(0, 100, 10))
    plt.show()
