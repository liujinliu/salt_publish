#coding=utf-8

import salt.client
import os
import logging
from config_parse import get_config

EXCUTE_CMD = 'cmd'
CHECK_CMD = 'check_cmd'
ESPECT = 'check_espect'

class LePublish(object):
    
    
    def __init__(self, salt_key, config_path,
                 module = 'example', extra = {},
                 action='update'):
        self.salt_key = salt_key
        self.extra = extra
        self.client = salt.client.LocalClient()
        self.playbook = os.path.join(
            config_path, module, ('%s.yml' %action))

    def pre_step(self):
        ret = self.client.cmd(self.salt_key, 'test.ping')
        if not ret:
            return False
        for _, v in ret.items():
            if not v:
                return False
        return True

    def get_steps(self):
        steps = get_config(self.playbook)
        for step in steps:
            step_name, = tuple(step)
            yield step_name, step[step_name]

    def _check_cmd(self, step):
        cmd = step[CHECK_CMD] % self.extra
        espect = step[ESPECT]
        ret = self.client.cmd(self.salt_key,
                'cmd.run', [cmd])
        tr, fa = espect.get(True,None), espect.get(False,None)
        tr = tr % self.extra if tr else tr
        fa = fa % self.extra if fa else fa
        for _, v in ret.items():
            if fa and v.find(fa)>=0:
                return False
            if tr and v.find(tr)>=0:
                continue
        return True

    def _excute_one_step(self, step):
        cmd = step[EXCUTE_CMD] % self.extra
        self.client.cmd(self.salt_key,
            'cmd.run', [cmd])
        if step.has_key(CHECK_CMD):
            return self._check_cmd(step)
        return True
        
    def publish(self):
        if not self.pre_step():
            return False
        for step_name, step_process in self.get_steps():
            for cmds in step_process:
                _cmds = cmds['excute']
                if not self._excute_one_step(_cmds):
                    return False
        return True

if __name__ == '__main__':
    le = LePublish('target-host',
         '../playbooks',
         extra=dict(filename='tmpfile'))
    print le.publish()

