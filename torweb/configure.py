#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

import os
import re
import yaml
import logging

inner_pattern = re.compile('\{\w+[\.\w+]*\}')

class ConfigLoader(object):
    config_path = None
    base_path = ""

    def __init__(self):
        self.config = None

    def load_environment(self):
        self.config['project_path'] = self.base_path

    def get_config_path(self):
        if not ConfigLoader.config_path:
            ConfigLoader.config_path = os.path.join(self.base_path, 'config')
        return ConfigLoader.config_path

    def get_config_file(self, name):
        import os.path

        #return os.path.join(self.get_config_path(), '%s.yaml' % name)
        return os.path.join(self.get_config_path(), '%s' % name)

    def load(self, config_file):
        self.config = self.load_file(config_file)
        self.load_environment()
        self.load_dynamic(self.config)
        return self.config
    def load_path(self, config_path):
        self.config = self.load_file(config_path)
        self.load_environment()
        self.load_dynamic(self.config)
        return self.config

    def load_file(self, config_file):
        config = {}
        try:
            with open(self.get_config_file(config_file), 'rb') as f:
                config = yaml.load(f)
                self.load_import(config)
        except Exception:
            logging.error("Uncaught Exception in load_file", exc_info=True)
        return config

    def load_dynamic(self, config):
        for key, value in config.iteritems():
            if isinstance(value, dict):
                self.load_dynamic(value)
                continue

            if not isinstance(value, basestring):
                continue

            matches = inner_pattern.findall(value)
            if not matches:
                continue
            while matches:
                for match in matches:
                    config[key] = re.sub(match, str(self.getConfig(match[1:-1])), config[key])
                matches = inner_pattern.findall(config[key])

    def load_import(self, config):
        if not 'import' in config:
            return config
        import_files = config['import']
        if import_files and (isinstance(import_files, set) or isinstance(import_files, list)):
            for import_file in import_files:
                self.import_single(config, import_file)
        return config

    def combile(self, config, import_config):
        for key, value in import_config.iteritems():
            if key == 'import' and 'import' in config:
                config['import'].extend(value)
                continue

            if not key in config:
                config[key] = value
            elif isinstance(value, dict) and isinstance(config[key], dict):
                self.combile(config[key], value)

    def import_single(self, config, import_file):
        import_config = self.load_file(import_file)
        self.combile(config, import_config)
        return config

    def getConfig(self, key):
        # every key is upper case
        key_no_case = key.lower()
        # split the string by .
        subkeys = re.split(r'\.', key_no_case)
        current_config = self.config
        for subkey in subkeys:
            assert (current_config is not None and isinstance(current_config, dict))
            current_config = current_config[subkey]
        return current_config

def get_host_ip():
    ip_addr = None
    import platform

    try:
        if platform.system() == 'Windows':
            import socket
            ip_addr = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        # 暂时将mac等同于linxu
        else:
            import fcntl
            import struct
            import socket
            def get_ip_address(ifname):
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                return socket.inet_ntoa(fcntl.ioctl(
                    s.fileno(),
                    0x8915, # SIOCGIFADDR
                    struct.pack('256s', ifname[:15])
                )[20:24])

            ip_addr = get_ip_address('eth0')
    except:
        pass

    return ip_addr


class Configuration(object):
    config_context = None

    def __init__(self, config_path):
        if not self.config_context:
            #self.config_context = ConfigLoader().load(config_entry_file)
            self.config_context = ConfigLoader().load_path(config_path)

    def getConfig(self, key):
        #Configuration.init()
        # every key is upper case
        key_no_case = key.lower()
        # split the string by .
        subkeys = re.split(r'\.', key_no_case)
        current_config = self.config_context
        for subkey in subkeys:
            assert (current_config is not None and isinstance(current_config, dict))
            current_config = current_config[subkey]
        return current_config


#configuration = Configuration()
#def CONF(key):
#    """
#     get the configuration value
#    """
#    return configuration.getConfig(key)
#    #return Configuration.getConfig(key)

class CONFIG(object):
    configuration = None
    def __init__(self, path):
        self.configuration = Configuration(path)
    def __call__(self, key):
        return self.configuration.getConfig(key)
