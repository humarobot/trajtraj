import yaml
import yamlordereddictloader


class ConfigParser:

    def __init__(self, file_path):
        self.file_name = file_path
        with open(file_path, 'r') as config:
            self.config = yaml.load(config, Loader=yamlordereddictloader.Loader)
            # self.config = yaml.load(config)
            # print self.config
        self.flatten_nested_list(self.config)
    def flatten_nested_list(self, input):
        if input is not None:
            for key, value in list(input.items()):
                # print key, value
                if isinstance(value, dict):
                    self.flatten_nested_list(value)
                if isinstance(value, (list, tuple)):
                    # print key, np.asarray(value)
                    if key in input:
                        input[key] = self.__flatten__(value)





    def get_by_key(self, key):
        if self.config is not None:
            if key in self.config:
                self.key = key
                return self.config[key]

    def __flatten__(self, l):
        return self.__flatten__(l[0]) + (self.__flatten__(l[1:]) if len(l) > 1 else []) if type(l) is list else [l]

    def merge_sub_groups(self, from_, what_):
        for value in self.config[self.key][from_]:
            value[what_] = self.flatten(value[what_])

    def save(self, default_flow_style=False):
        with open(self.file_name, 'w') as yaml_file:
            yaml.dump(self.config, yaml_file, default_flow_style=default_flow_style,
                      Dumper=yamlordereddictloader.Dumper)

    @classmethod
    def save_to_file(self, file_name, data, mode="w", default_flow_style=False):
        with open(file_name, mode) as yaml_file:
            yaml.dump(data, yaml_file, default_flow_style=default_flow_style,
                      Dumper=yamlordereddictloader.Dumper)