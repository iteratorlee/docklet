from utils.log import initlogging, logger
from numpy import random as rd
from collections import defaultdict
import json

class StorageMgr(object):
    def __init__(self):
        self.client_bin_path = '/usr/bin/akame-client'
        self.server_bin_path = '/usr/bin/akame-server'

    def list_dataset(self, user):
        logger.debug('list_dataset entered')
        try:
            dataset_list = []
            for i in range(10):
                tmp_dataset_info = defaultdict(lambda: '')
                tmp_dataset_info['name'] = 'dataset_' + str(i)
                tmp_dataset_info['update_time'] = '2018-10-26'
                tmp_dataset_info['version'] = '1.0'
                tmp_dataset_info['size'] = str(int(rd.randn() * 30 + 500)) + ' MB'
                tmp_dataset_info['status'] = 'imported' if rd.randn() > 0.5 else 'cloud'
                tmp_dataset_info['type']  = 'public' if rd.randn() > 0.5 else 'private'
                dataset_list.append(tmp_dataset_info)
            #logger.debug('dataset_list: %s' % json.dumps({'data': dataset_list}, indent=4))
            return {
                'status': True,
                'message': '',
                'data' : dataset_list
            }
        except Exception as err:
            return {
                'status': False,
                'message': err.args[0],
                'data': ''
            }