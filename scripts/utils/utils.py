import numpy as np
from itertools import tee, islice, chain, cycle
import math
import logging
import rospkg
import sys


class Utils:

    #  https://stackoverflow.com/questions/1011938/python-previous-and-next-values-inside-a-loop
    @classmethod
    def iterate_with_previous_and_next(cls, some_iterable):
        prevs, items, nexts = tee(some_iterable, 3)
        prevs = chain([None], prevs)
        nexts = chain(islice(nexts, 1, None), [None])
        return zip(prevs, items, nexts)

    # https://stackoverflow.com/questions/323750/how-to-access-previous-next-element-while-for-looping
    @classmethod
    def neighborhood(cls, iterable):
        # iterator = iter(iterable)
        iterator = cycle(iterable)
        prev_item = None
        current_item = next(iterator)  # throws StopIteration if empty.
        for next_item in iterator:
            yield (prev_item, current_item, next_item)
            prev_item = current_item
            current_item = next_item
        yield (prev_item, current_item, None)

    @classmethod
    def interpolate(cls, start, end, samples=5, decimals_to_round=3):
        data = []
        step_size = (end - start) / (samples - 1)
        intermediate = start
        for i in range(samples):
            data.append(intermediate)
            intermediate += step_size
        return np.round(data, decimals_to_round)

    # https://stackoverflow.com/questions/21030391/how-to-normalize-an-array-in-numpy
    @classmethod
    def normalize_vector(cls, vector):
        norm = np.linalg.norm(vector, ord=1)
        if norm == 0:
            norm = np.finfo(vector.dtype).eps
        return vector / norm

    # https://stackoverflow.com/questions/4114921/vector-normalization
    @classmethod
    def normalize_vector1(cls, vector):
        vector_magnitude = math.sqrt(sum(vector[i] * vector[i] for i in range(len(vector))))
        # return [vector[i] / vector_magnitude for i in range(len(vector))]
        if vector_magnitude == 0:
            vector_magnitude = 0.00001
        for i in range(len(vector)):
            vector[i] =  vector[i] / vector_magnitude
        return vector

    @classmethod
    def __diagonal_block_mat_slicing(self, matrix):
        shape = matrix[0].shape
        length = len(matrix)
        length_range = list(range(length))
        out = np.zeros((length, shape[0], length, shape[1]), dtype=int)
        out[length_range, :, length_range, :] = matrix
        return out.reshape(np.asarray(shape) * length)

    @classmethod
    def interpolate_list(cls, input_list, samples=3):
        new_list = []
        for prev_elt, current_elt, next_elt in cls.iterate_with_previous_and_next(input_list):
            if next_elt is not None:
                if type(current_elt) is list:
                    cls.interpolate_list(current_elt, samples)
                new_list += cls.interpolate(current_elt, next_elt, samples).tolist()
        print(input_list)
        print(new_list)
        return new_list

    @classmethod
    def setup_logger(self, logger, main_logger_name, verbose=False, log_file=False):

        # creating a formatter
        formatter = logging.Formatter('-%(asctime)s - %(name)s - %(levelname)-8s: %(message)s')

        # create console handler with a debug log level
        log_console_handler = logging.StreamHandler()
        if log_file:
            # create file handler which logs info messages
            logger_file_handler = logging.FileHandler(main_logger_name + '.log', 'w', 'utf-8')
            logger_file_handler.setLevel(logging.INFO)
            # setting handler format
            logger_file_handler.setFormatter(formatter)
            # add the file logging handlers to the logger
            logger.addHandler(logger_file_handler)

        if verbose == "WARN":
            logger.setLevel(logging.WARN)
            log_console_handler.setLevel(logging.WARN)

        elif verbose == "INFO" or verbose is True:
            logger.setLevel(logging.INFO)
            log_console_handler.setLevel(logging.INFO)

        elif verbose == "DEBUG":
            logger.setLevel(logging.DEBUG)
            log_console_handler.setLevel(logging.DEBUG)

        # setting console handler format
        log_console_handler.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(log_console_handler)

    @classmethod
    def replace_none(cls, x, v, negate=False):
        if x is None:
            return v if not negate else -v
        return x

    @classmethod
    def replace_paths(cls, urdf_file):
        with open(urdf_file, 'r') as f:
            urdf_str = f.read().replace('\n', '')
        rospack = rospkg.RosPack()
        with open('/tmp/robot.urdf', 'w') as o:
            for line in urdf_str.split('\n'):
                if 'package://' in line:
                    package_name = line.split('package://', 1)[-1].split('/', 1)[0]
                    real_path = rospack.get_path(package_name)
                    o.write(line.replace(package_name, real_path))
                else:
                    o.write(line)
    @classmethod
    def replace_paths_(cls, urdf_file):
        with open(urdf_file, 'r') as f:
            urdf_str = f.read().replace('\n', '')
        rospack = rospkg.RosPack()
        urdf_string_with_abs_path = ""
        for line in urdf_str.split('\n'):
            if 'package://' in line:
                package_name = line.split('package://', 1)[-1].split('/', 1)[0]
                real_path = rospack.get_path(package_name)
                urdf_string_with_abs_path += line.replace(package_name, real_path)
            else:
                urdf_string_with_abs_path += line
        return urdf_string_with_abs_path

    @classmethod
    def get_var_from_kwargs(cls, key, optional=False, default=None, **kwargs):
        if key in kwargs:
            return kwargs[key]
        elif optional and default is not None:
            return default
        elif not optional:
            method_name = sys._getframe().f_back.f_code.co_name
            raise Exception("Method: \"" + method_name + "\" expects a parameter with key: " + str(key))
        else:
            return None