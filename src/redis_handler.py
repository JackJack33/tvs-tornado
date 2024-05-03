import logging
import os
import uuid
from typing import Union
import redis
import pandas as pd
from hotqueue import HotQueue


class RedisEnum:
    """
    Enum class to signal which database to target
    """
    DATA = 0
    JOBS = 1
    RESULTS = 2


class RedisHandler:
    def __init__(self):
        # if 'REDIS_IP' not in os.environ:
        #     raise KeyError('REDIS_IP environment variable is not defined.')
        ip = os.getenv('REDIS_IP', 'localhost')
        self.__db = [redis.Redis(host=ip, port=6379, db=num) for num in range(3)]
        self.__q = HotQueue('queue', host=ip, port=6379, db=3)

    def get_all_data(self):
        """
        Retrieve all data from TVS warning data Redis database.

        :return:
        """
        keys = self.get_keys(RedisEnum.DATA)
        if len(keys) == 0:
            raise EnvironmentError('No data in Redis database.')
        return [{key.decode(): val.decode() for key, val in self.__db[RedisEnum.DATA].hgetall(rd_key).items()} for rd_key in keys]

    def post_tvs_data(self, url: str):
        """
        Pull data from given URL and upload it to Redis database.

        :param url:     str     URL to pull data from
        """
        pd.read_csv(url, header=2, compression='gzip').apply(
            lambda row: self.__db[RedisEnum.DATA].hset(str(uuid.uuid4()), mapping=dict(row)), axis=1)

    def get_keys(self, db_enum: int) -> list:
        """
        Retrieve all keys from a particular Redis database.

        :param db_enum:     int     RedisEnum database value
        :return:            list    All keys decoded into strings of the given db_enum
        """
        return [val.decode() for val in self.__db[db_enum].keys()]

    def delete_db(self, db_enum: int):
        """
        Delete all information from a particular Redis database.

        :param db_enum:     int     RedisEnum database value
        """
        for key in self.get_keys(db_enum):
            self.__db[db_enum].delete(key)

    def set(self, db_enum: int, key, val: Union[dict, bytes, memoryview, str, int, float]):
        """
        Redis.redis.set/hset wrapper. Can take in a dict and assign the entire thing as a hash, set a value of an
        existing hash by taking in a tuple containing (hash name, value), or set a singular value.

        :param db_enum:     int         RedisEnum database value
        :param key:         str         Key name to set
        :param val:         tuple | *   Value to set or tuple containing (hash name, value to set)
        """
        if isinstance(val, dict):
            self.__db[db_enum].hset(key, mapping=val)
        elif isinstance(val, tuple) and len(val) == 2:
            self.__db[db_enum].hset(key, *val)
        else:
            self.__db[db_enum].set(key, val)

    def get(self, db_enum: int, key: str, is_dict: bool = False):
        """
        Retrieve a value from a particular key from a particular Redis database.

        :param db_enum:     int         RedisEnum database value
        :param key:         str         Key name to get
        :param is_dict:     bool        Determines whether to get all values of a hash or an individual value

        :return:            dict | *    If is_dict, returns hash as a dict, otherwise the individual value
        """
        return self.__db[db_enum].hgetall(key) if is_dict else self.__db[db_enum].get(key)

    def hget(self, db_enum: int, name: str, key: str):
        """
        Retrieve a value from a particular key/hash pair from a particular Redis database.

        :param db_enum:     int         RedisEnum database value
        :param name:        str         Key name to get
        :param key:         str         Hash key name
        :return:            *           Individual value
        """
        return self.__db[db_enum].hget(name, key)

    def add_job(self, job_info):
        """
        Creates a new job in the Redis database and adds it to the queue.

        :param job_info:    dict        dictionary containing information from inputs of webpage
        :return:            str         UUID of job
        """
        jid = str(uuid.uuid4())
        job_info['id'] = jid
        job_info['status'] = 'Submitted'
        self.__db[RedisEnum.JOBS].hset(jid, mapping=job_info)
        self.__q.put(job_info)
        return jid

    def _get_q_obj(self):
        """
        Returns queue object to be used programmatically.

        :return:            HotQueue    queue instance
        """
        return self.__q


if __name__ == '__main__':
    handler = RedisHandler()
