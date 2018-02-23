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
        oss_passwd_file = 'test-passwd-ossfs'
        #oss_passwd_file = '/etc/passwd-ossfs'
        with open(oss_passwd_file, 'aw+') as fd:
            new_ak = bucket_name + ':' + access_id + ':' + access_key + '\n'
            fd.write(new_ak)
        os.chmod(oss_passwd_file, stat.S_IRUSR + stat.S_IWUSR + stat.S_IRGRP)

    @classmethod
    def mount_oss(self, bucket_name, mount_path, endpoint):
        if not os.path.exists(mount_path):
            error_msg = 'oss mount path "%s" does not exist!' % mount_path
            return error_msg
        else:
            cmd = 'ossfs ' + bucket_name + ' ' + mount_path + ' -ourl=' + endpoint
            prog = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            msg = prog.stdout.read().decode()
            return msg

    @classmethod
    def umount_oss(self, mount_path):
        if not os.path.exists(mount_path):
            error_msg = 'oss mount path "%s" does not exist!' % mount_path
            return error_msg
        else:
            cmd = 'umount ' + mount_path
            prog = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            msg = prog.stdout.read().decode()
            return msg

    @classmethod
    def mount(self, **kwargs):
        mount_path = kwargs['mount_path']
        bucket_name = kwargs['bucket_name']
        endpoint = kwargs['endpoint']
        access_id = kwargs['access_id']
        access_key = kwargs['access_key']
        self.add_oss_ak(bucket_name, access_id, access_key)
        self.mount_oss(bucket_name, mount_path, endpoint)

    @classmethod
    def unmount(self, **kwargs):
        mount_path = kwargs['mount_path']
        self.umount_oss(self, mount_path)