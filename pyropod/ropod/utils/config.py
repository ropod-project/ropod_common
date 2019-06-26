import yaml


def read_yaml_file(config_file_name):
    file_handle = open(config_file_name, 'r')
    data = get_config(file_handle)
    file_handle.close()
    return data


def get_config(yaml_file):
    data = yaml.safe_load(yaml_file)
    return data
