import yaml


def read_yaml_file(config_file_name):
    file_handle = open(config_file_name, 'r')
    data = yaml.safe_load(file_handle)
    file_handle.close()
    return data
