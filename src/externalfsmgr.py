import os
import stat
import sys
import subprocess
from log import logger

class ExternalFSManager(object):
    '''
    Handle the mounting of external file system
    '''
    @classmethod
    def mount(self, **kwargs):
        pass

    @classmethod
    def unmount(self, **kwargs):
        pass


class AliyunOSSManager(ExternalFSManager):
    '''
    Handle the mounting of aliyun oss
    '''
    @classmethod
    def add_oss_ak(self, bucket_name, access_id, access_key):
        #oss_passwd_file = 'test-passwd-ossfs'
        oss_passwd_file = '/etc/passwd-ossfs'
        all_aks = []
        with open(oss_passwd_file, 'r') as fd:
            all_aks = fd.readlines()

        new_ak = bucket_name + ':' + access_id + ':' + access_key + '\n'
        if not new_ak in all_aks:
            with open(oss_passwd_file, 'a+') as fd:
                fd.write(new_ak)
                logger.info('new aliyun oss access_key added, bucket_name: %s' % bucket_name)
        else:
            logger.info('access_key already exists')

        os.chmod(oss_passwd_file, stat.S_IRUSR + stat.S_IWUSR + stat.S_IRGRP)

    @classmethod
    def mount_oss(self, bucket_name, mount_path, endpoint):
        logger.info('mount_oss function entered')
        if not os.path.exists(mount_path):
            logger.info('oss mount path "%s" does not exist, trying to create' % mount_path)
            try:
                os.makedirs(mount_path)
            except Error:
                error_msg = ('create mount path %s error' % mount_path)
                return False, error_msg

        mount_cmd = 'ossfs ' + bucket_name + ' ' + mount_path + ' -ourl=' + endpoint + ' -o allow_other'
        prog = subprocess.Popen(mount_cmd, shell=True, stderr=subprocess.PIPE)
        msg = prog.stderr.read().decode()
        if msg != '':
            return False, msg
        else:
            logger.info('aliyun oss mounted: bucket_name: %s, mount_path %s, endpoint: %s' \
                        % (bucket_name, mount_path, endpoint))
            if mount_path[-1] != '/':
                mount_path += '/*'
            else:
                mount_path += '*'
            
            chmod_cmd = 'chmod -R 777 ' + mount_path
            prog = subprocess.Popen(chmod_cmd, shell=True, stderr=subprocess.PIPE)
            msg = prog.stderr.read().decode()
            if msg != '':
                return False, msg
            return True, ''

    @classmethod
    def umount_oss(self, mount_path):
        if not os.path.exists(mount_path):
            error_msg = 'oss mount path "%s" does not exist!' % mount_path
            return False, error_msg
        else:
            cmd = 'umount ' + mount_path
            prog = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
            msg = prog.stderr.read().decode()
            if msg != '':
                return False, msg
            else:
                logger.info('aliyun oss unmounted: mount_path: %s' % mount_path)
                return True, msg

    @classmethod
    def mount(self, **kwargs):
        mount_path = kwargs['mount_path']
        bucket_name = kwargs['bucket_name']
        endpoint = kwargs['endpoint']
        access_id = kwargs['access_id']
        access_key = kwargs['access_key']
        self.add_oss_ak(bucket_name, access_id, access_key)
        status, msg = self.mount_oss(bucket_name, mount_path, endpoint)
        if not status:
            logger.error('mount failed: ', msg)
            return [False, msg]
        else:
            return [True, msg]

    @classmethod
    def unmount(self, **kwargs):
        mount_path = kwargs['mount_path']
        status, msg = self.umount_oss(mount_path)
        if not status:
            logger.error('unmount failed: ', msg)
            return [False, msg]
        else:
            return [True, msg]
