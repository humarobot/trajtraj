import logging
from scripts.utils.utils import Utils as utils
from urdf_parser_py.urdf import URDF
from scripts.Robot.Planner import TrajectoryPlanner
import itertools
from srdfdom.srdf import SRDF
from scripts.utils.dict import DefaultOrderedDict
from collections import OrderedDict


class Robot:
    def __init__(self, logger_name=__name__, verbose=False, log_file=False):
        self.id = -1
        self.model = None
        self.planner = TrajectoryPlanner(logger_name, verbose, log_file)
        self.logger = logging.getLogger(logger_name + __name__)
        self.ignored_collisions = DefaultOrderedDict(bool)
        self.srdf = None
        self.group_states_map = OrderedDict()
        self.joint_states_map = OrderedDict()
        self.group_map = OrderedDict()
        utils.setup_logger(self.logger, logger_name, verbose, log_file)

    # method to load robot model from urdf file
    def load_robot_model(self, urdf_file=None):
        if urdf_file is not None:
            self.model = URDF.from_xml_file(urdf_file)
        else:
            self.model = URDF.from_parameter_server()

    # method to load robot' configurations from srdf file
    def load_srdf(self, srdf_file):

        stream = open(srdf_file, 'r')
        self.srdf = SRDF.from_xml_string(stream.read())
        for gs in self.srdf.group_states:
            joint_map = OrderedDict()
            for joint in  gs.joints:
                joint_map[joint.name] = joint.value[0]
            self.group_states_map[gs.name, gs.group] = joint_map
            self.joint_states_map[gs.name] = joint_map
            self.group_map[gs.group] = list(joint_map.keys())

    def get_ignored_collsion(self):
        for collision in self.srdf.disable_collisionss:
            self.ignored_collisions[collision.link1, collision.link2] = True
            self.ignored_collisions[collision.link2, collision.link1] = True

        return self.ignored_collisions

    # given a planning group and name of the configuration to be moved, corresponding joint states will be returned
    def get_planning_group_joint_values(self, name, group):
        joint_state = OrderedDict()
        if (name, group) in self.group_states_map:
            joint_state = self.group_states_map[name, group]
        return list(joint_state.keys()), list(joint_state.values())

    # planning group name as string to joint names list
    def get_planning_group_from_srdf(self, group):
        if group in self.group_map:
            group = self.group_map[group]
        return group

    # planning group name as string to joint states list
    def get_group_state_from_srdf(self, group_name):
        joint_state = OrderedDict()
        if group_name in self.joint_states_map:
            joint_state = self.joint_states_map[group_name]
        return list(joint_state.keys()), list(joint_state.values())

    # returns final planned trajectory
    def get_trajectory(self):
        return self.planner.trajectory

    # returns initial guess for trajectory calculation
    def get_initial_trajectory(self):
        return self.planner.trajectory.initial

    # method to model the problem and to initialize the SQP solver
    def init_plan_trajectory(self, **kwargs):
        joint_group = utils.get_var_from_kwargs("group", **kwargs)
        samples = utils.get_var_from_kwargs("samples", **kwargs)
        duration = utils.get_var_from_kwargs("duration", **kwargs)
        solver = utils.get_var_from_kwargs("solver", optional=True, default="SCS", **kwargs)
        solver_config = utils.get_var_from_kwargs("solver_config", optional=True, **kwargs)

        # some default config for the SQP solver
        if solver_config is not None:
            if "decimals_to_round" in solver_config:
                decimals_to_round = int(solver_config["decimals_to_round"])
        else:
            decimals_to_round = 5

        current_state = utils.get_var_from_kwargs("current_state", **kwargs)
        goal_state = utils.get_var_from_kwargs("goal_state", **kwargs)

        collision_safe_distance = utils.get_var_from_kwargs("collision_safe_distance", optional=True,
                                                            default=0.05, **kwargs)

        collision_check_distance = utils.get_var_from_kwargs("collision_check_distance", optional=True,
                                                            default=0.1, **kwargs)
        ignore_goal_states = utils.get_var_from_kwargs("ignore_goal_states", optional=True, **kwargs)

        solver_class = utils.get_var_from_kwargs("solver_class", optional=True, default="new", **kwargs)

        verbose = utils.get_var_from_kwargs("verbose", optional=True, default=False, **kwargs)

        # combing all necessary infos to model and plan a trajectory
        if "current_state" in kwargs and "goal_state" in kwargs:
            if type(current_state) is dict and type(current_state) is dict:
                states = {}
                joints = {}
                for joint_in_group in joint_group:
                    if joint_in_group in current_state and joint_in_group in goal_state and \
                                    joint_in_group in self.model.joint_map:
                        if self.model.joint_map[joint_in_group].type != "fixed":
                            ignore_state = False
                            if joint_in_group in ignore_goal_states:
                                ignore_state = True
                            states[joint_in_group] = {"start": current_state[joint_in_group],
                                                      "end": goal_state[joint_in_group]}
                            joints[joint_in_group] = {
                                "states": states[joint_in_group],
                                "limit": self.model.joint_map[joint_in_group].limit,
                                "ignore_state": ignore_state
                            }
            elif type(current_state) is list and type(current_state) is list:
                joints = []

                assert len(current_state) == len(goal_state) == len(joint_group)
                for joint, c_state, n_state in zip(joint_group, current_state, goal_state):
                    if joint in self.model.joint_map:
                        ignore_state = False
                        if ignore_goal_states is not None and len(ignore_goal_states):
                            if joint in ignore_goal_states:
                                ignore_state = True
                        joints.append([c_state, n_state, self.model.joint_map[joint].limit, ignore_state])
        if len(joints):
            # initializing the trajectory planner to model the problem
            self.planner.init(joints=joints, samples=samples, duration=duration,
                              joint_group=joint_group,
                              collision_safe_distance=collision_safe_distance,
                              collision_check_distance=collision_check_distance,
                              solver=solver, solver_config=solver_config,
                              solver_class=solver_class, decimals_to_round=decimals_to_round, verbose=verbose)

    def calulate_trajecotory(self, callback_function=None):
        status, planning_time, can_execute_trajectory = self.planner.calculate_trajectory(callback_function=callback_function)
        return status, planning_time, can_execute_trajectory



