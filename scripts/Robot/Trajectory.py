import numpy as np
from scripts.utils.dict import DefaultOrderedDict
from collections import OrderedDict
from scripts.plotter.results import Plotter as plt

class Trajectory:
    def __init__(self):
        self.__trajectory = -1
        self.__no_of_samples = -1
        self.__duration = -1
        self.__trajectory_by_joint_name = DefaultOrderedDict(list)
        self.__initial = None
        self.__trajectories = []
        self.__final = None
        self.__trajectory_group = None

    @property
    def trajectory(self):
        return self.__trajectory
    @property
    def trajectories(self):
        return self.__trajectories

    @property
    def initial(self):
        return self.__initial

    @property
    def final(self):
        return self.__final

    @property
    def duration(self):
        return self.__duration

    @property
    def no_of_samples(self):
        return self.__no_of_samples

    @property
    def trajectory_by_name(self):
        return self.__trajectory_by_joint_name
    @property
    def trajectory_group(self):
        return self.__trajectory_group

    # initializing initial trajectory guess for the SQP solver, number of samples and planning group
    def init(self, trajectory, no_of_samples, duration, group):
        self.__no_of_samples = no_of_samples
        self.__duration = duration
        self.__initial = np.array(trajectory).T
        self.__trajectory_group = group

    # updating final trajectory from the SQP solver
    def update(self, trajectory, group):
        self.__trajectory = trajectory
        self.__final = np.array(trajectory)
        self.extract_trajectory_of_individual_joints(group)
        self.add_trajectory(trajectory)

    # converting and combining list of trajectory to trajectory by joint name
    def extract_trajectory_of_individual_joints(self, group):
        self.__trajectory_by_joint_name = OrderedDict(list(zip(group, self.final.T)))

    # adding trajectory from each SQP iteration
    def add_trajectory(self, trajectory):
        self.__trajectories.append(OrderedDict(list(zip(self.trajectory_group, np.array(trajectory).T))))

    # to plot final result
    def plot_trajectories(self):
        plt.multi_plot(list(self.trajectory_by_name.keys()), self.initial, list(self.trajectory_by_name.values()),
                                  # "Time steps (t)", "Joint angle (q)", block=True)
                                  "Samples", "Joint angle ($\\Theta$)", block=True)