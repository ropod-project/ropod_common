import logging.config
import yaml
import pkg_resources


def config_logger(config_file=None, filename=None):

    if not config_file:
        config_file = yaml.load(pkg_resources.resource_filename('ropod.pyre_communicator', 'config/logging.yaml'))

    with open(config_file) as yaml_file:
        log_config = yaml.safe_load(yaml_file)

    if filename:
        log_config['handlers']['file']['filename'] = '/var/log/ropod/fms/%s.log' % filename

    logging.config.dictConfig(log_config)

