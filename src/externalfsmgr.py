import os
import stat
import sys
import subprocess
from log import logger

from updatebase import aufs_update_base

import oss2

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
        if os.path.exists(oss_passwd_file):
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
    def mount_oss(self, bucket_name, mount_path, mount_path_ro, mount_path_rw, endpoint):
        if not os.path.exists(mount_path_ro):
            logger.info('oss mount path "%s" does not exist, trying to create' % mount_path)
            try:
                os.makedirs(mount_path_ro)
            except Exception as e:
                error_msg = ('create mount path %s error' % mount_path)
                return False, error_msg

        mount_cmd = 'ossfs ' + bucket_name + ' ' + mount_path_ro + ' -ourl=' + endpoint + ' -o allow_other'
        prog = subprocess.Popen(mount_cmd, shell=True, stderr=subprocess.PIPE)
        msg = prog.stderr.read().decode()
        if msg != '':
            return False, msg
        else:
            logger.info('aliyun oss mounted: bucket_name: %s, mount_path %s, endpoint: %s' \
                        % (bucket_name, mount_path_ro, endpoint))
            if mount_path_ro[-1] != '/':
                mount_path_ro += '/*'
            else:
                mount_path_ro += '*'

            chmod_cmd = 'chmod -R 777 ' + mount_path_ro
            prog = subprocess.Popen(chmod_cmd, shell=True, stderr=subprocess.PIPE)
            msg = prog.stderr.read().decode()
            if msg != '':
                return False, msg
            else:
                mount_path_ro = mount_path_ro[:-1]
                return self.mount_aufs(mount_path_ro, mount_path_rw, mount_path)

    @classmethod
    def mount_aufs(self, ro_path, rw_path, mount_path):
        if not os.path.exists(rw_path):
            logger.info('aufs read/write path %s does not exist, trying to create' % rw_path)
            try:
                os.makedirs(rw_path)
            except Exception as e:
                error_msg = ('create aufs read/write path %s error' % rw_path)
                return False, error_msg
        if not os.path.exists(mount_path):
            logger.info('aufs mount path %s does not exist, trying to create' % mount_path)
            try:
                os.makedirs(mount_path)
            except Exception as e:
                error_msg = ('create aufs mount path %s error' % mount_path)
                return False, error_msg
        mount_cmd = 'mount -t aufs -o br=' + rw_path + '=rw:' + ro_path + '=ro none ' + mount_path
        prog = subprocess.Popen(mount_cmd, shell=True, stderr=subprocess.PIPE)
        msg = prog.stderr.read().decode()
        if msg != '':
            return False, msg
        else:
            logger.info('aufs mounted: ro_path: %s, rw_path: %s, mount_path: %s' % (ro_path, rw_path, mount_path))
            return True, msg

    @classmethod
    def umount_oss(self, mount_path, mount_path_ro, mount_path_rw):
        if not os.path.exists(mount_path):
            error_msg = 'aufs(oss) mount path "%s" does not exist!' % mount_path
            return False, error_msg
        else:
            cmd = 'umount ' + mount_path
            prog = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
            msg = prog.stderr.read().decode()
            if msg != '':
                return False, msg
            else:
                logger.info('aufs(oss) unmounted: mount_path: %s' % mount_path)
                return self.umount_oss_ro(mount_path_ro, mount_path_rw)

    @classmethod
    def umount_oss_ro(self, ro_path, rw_path):
        status, msg = self.sync_oss(ro_path, rw_path)
        if not status:
            return status, msg
        else:
            cmd = 'umount ' + ro_path
            prog = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
            msg = prog.stderr.read().decode()
            if msg != '':
                return False, msg
            else:
                logger.info('ossfs unmounted: mount_path: %s' % ro_path)
                return True, msg

    @classmethod
    def sync_oss(self, ro_path, rw_path):
        aufs_update_base(rw_path, ro_path)
        return True, ''

    @classmethod
    def mount(self, **kwargs):
        mount_path = kwargs['mount_path']
        mount_path_ro = kwargs['mount_path_ro']
        mount_path_rw = kwargs['mount_path_rw']
        bucket_name = kwargs['bucket_name']
        endpoint = kwargs['endpoint']
        access_id = kwargs['access_id']
        access_key = kwargs['access_key']
        self.add_oss_ak(bucket_name, access_id, access_key)
        status, msg = self.mount_oss(bucket_name, mount_path, mount_path_ro, mount_path_rw, endpoint)
        if not status:
            logger.error('mount failed: ', msg)
            return [False, msg]
        else:
            return [True, msg]

    @classmethod
    def unmount(self, **kwargs):
        mount_path = kwargs['mount_path']
        mount_path_ro = kwargs['mount_path_ro']
        mount_path_rw = kwargs['mount_path_rw']
        status, msg = self.umount_oss(mount_path, mount_path_ro, mount_path_rw)
        if not status:
            logger.error('unmount failed: ', msg)
            return [False, msg]
        else:
            return [True, msg]

class AliyunOSSManagerInternal(ExternalFSManager):
    '''
    An implementation of mounting Aliyun OSS Service to the workspace
    to adapt running data processing programs in Docklet.
    In current Docklet version, the user need to syncronize their cloud
    files mannually.
    '''
    @classmethod
    def list_objs(self, bucket, prefix=''):
        objs = {}
        if prefix == '':
            for obj in oss2.ObjectIterator(bucket, delimiter='/'):
                file_meta = {}
                if obj.is_prefix():
                    file_meta['type'] = 'dir'
                else:
                    file_meta['type'] = 'file'
                objs[obj.key] = file_meta
        else:
            for obj in oss2.ObjectIterator(bucket, prefix=prefix):
                file_meta = {}
                obj_name = obj.key[len(prefix):]
                if obj_name == "":
                    continue
                if '/' in obj_name:
                    obj_name = obj_name.split('/')[0] + '/'
                    if obj_name in objs:
                        continue
                    file_meta['type'] = 'dir'
                else:
                    file_meta['type'] = 'file'
                objs[obj_name] = file_meta

        return objs

    @classmethod
    def trace_objs(self, bucket, prefix=''):
        objs = self.list_objs(bucket, prefix)
        print('prefix : %s' % prefix)
        print(json.dumps(objs, indent=4))
        for key in objs:
            if objs[key]['type'] == 'dir':
                trace_objs(bucket, prefix + key)

    @classmethod
    def get_bucket(self, access_id, access_key, endpoint, bucket_name):
        auth = oss2.Auth(access_id, access_key)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        return bucket

    @classmethod
    def mount(self, **kwargs):
        mount_path = kwargs['mount_path']
        bucket_name = kwargs['bucket_name']
        endpoint = kwargs['endpoint']
        access_id = kwargs['access_id']
        access_key = kwargs['access_key']
        bucket = self.get_bucket(access_id, access_key, endpoint, bucket_name)
        pass

    @classmethod
    def unmount(self, **kwargs):
        pass
