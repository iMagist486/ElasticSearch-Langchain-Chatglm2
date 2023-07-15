# -*- coding: UTF-8 -*-
from configparser import ConfigParser


class BaseParams(object):
    """
    各类型参数的父类
    """

    def __init__(self, conf_fp: str = 'configs/config.ini'):
        self.config = ConfigParser()
        self.config.read(conf_fp, encoding='utf8')


class ModelParams(BaseParams):
    """
    数据拉取参数类
    """

    def __init__(self, conf_fp: str = 'configs/config.ini'):
        super(ModelParams, self).__init__(conf_fp)
        section_name = 'model_configs'
        self.embedding_model = self.config.get(section_name, 'embedding_model')
        self.llm_model = self.config.get(section_name, 'llm_model')


class ESParams(BaseParams):
    """
    数据拉取参数类
    """

    def __init__(self, conf_fp: str = 'configs/config.ini'):
        super(ESParams, self).__init__(conf_fp)
        section_name = 'es_configs'
        self.username = self.config.get(section_name, 'username')
        self.passwd = self.config.get(section_name, 'passwd')
        self.url = self.config.get(section_name, 'url')
        self.port = self.config.get(section_name, 'port')
        self.index_name = self.config.get(section_name, 'index_name')
