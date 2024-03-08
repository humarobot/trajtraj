from PySide6 import QtWidgets
from scripts.utils import yaml_paser as yaml
import functools
from scripts.utils.utils import Utils as utils
import logging
import os


class PlannerGui(QtWidgets.QMainWindow):
    def __init__(self, logger_name=__name__, config_file=None, verbose=False, file_log=False, planner=None, width=900, height=400):
        QtWidgets.QMainWindow.__init__(self)
        self.setGeometry(200, 100, width, height)

        # self.sim_world = SimulationWorld.SimulationWorld(self.robot_config["urdf"])
        self.planner = planner

        if config_file is None:
            dirname = os.path.dirname(__file__)
            file_path_prefix = os.path.join(dirname, '../../config/')
            # file_path_prefix = '../../config/'
            config_file = file_path_prefix + 'default_config.yaml'

        self.default_config = yaml.ConfigParser(config_file)
        self.config = self.default_config.get_by_key("config")

        self.sqp_config_file = file_path_prefix + self.config["solver"]

        self.sqp_yaml = yaml.ConfigParser(self.sqp_config_file)
        self.sqp_config = self.sqp_yaml.get_by_key("sqp")
        robot_config_file = file_path_prefix + self.config["robot"]["config"]
        self.robot_default_config_params = self.config["robot"]["default_paramaters"]
        robot_yaml = yaml.ConfigParser(robot_config_file)
        self.robot_config = robot_yaml.get_by_key("robot")

        self.sqp_labels = {}
        self.sqp_spin_box = {}
        self.sqp_combo_box = {}

        self.sqp_config_group_box = QtWidgets.QGroupBox('SQP solver Parameters')
        self.sqp_config_form = QtWidgets.QFormLayout()

        self.sqp_config_scroll = QtWidgets.QScrollArea()

        self.robot_config_params = {}
        self.robot_config_labels = {}
        self.robot_config_spin_box = {}
        self.robot_config_combo_box = {}
        self.robot_config_params_spin_box = {}
        self.robot_config_group_box = QtWidgets.QGroupBox('Robot Actions')
        self.simulation_action_group_box = QtWidgets.QGroupBox('Simulation')

        self.robot_config_hbox = QtWidgets.QVBoxLayout()

        self.robot_config_vbox_layout = QtWidgets.QVBoxLayout()

        self.robot_config_form = QtWidgets.QFormLayout()

        self.robot_action_buttons = {}
        self.robot_action_button_group = QtWidgets.QButtonGroup(self)
        self.robot_action_buttons["execute"] = QtWidgets.QPushButton('Execute')
        self.robot_action_buttons["plan"] = QtWidgets.QPushButton('Plan')
        self.robot_action_buttons["random_pose"] = QtWidgets.QPushButton('Random Pose')
        self.robot_action_buttons["plan_and_execute"] = QtWidgets.QPushButton('Plan and Execute')
        self.robot_action_button_hbox = QtWidgets.QHBoxLayout()

        self.robot_config_scroll = QtWidgets.QScrollArea()

        self.selected_robot_combo_value = {}
        self.selected_robot_spin_value = {}

        self.statusBar = QtWidgets.QStatusBar()

        self.main_widget = QtWidgets.QWidget(self)
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_hbox_layout = QtWidgets.QHBoxLayout()

        self.last_status = "Last Status: "
        self.init_ui(25)

        self.can_execute_trajectory = False
        self.logger = logging.getLogger(logger_name + __name__)
        utils.setup_logger(self.logger, logger_name, verbose, file_log)


    def init_ui(self, val):

        self.main_widget.setLayout(self.main_layout)
        self.main_layout.addLayout(self.main_hbox_layout)
        self.main_layout.addStretch(1)
        self.setCentralWidget(self.main_widget)
        self.setStatusBar(self.statusBar)

        max_sqp_config = 1e4

        for key, value in list(self.sqp_config.items()):
            self.sqp_labels[key] = QtWidgets.QLabel(key)
            if not isinstance(value, list):
                self.sqp_spin_box[key] = QtWidgets.QDoubleSpinBox(self)

            else:
                self.sqp_combo_box[key] = QtWidgets.QComboBox(self)

        for key in self.sqp_labels:
            if not isinstance(self.sqp_config[key], list):
                self.sqp_config_form.addRow(self.sqp_labels[key], self.sqp_spin_box[key])
                self.sqp_spin_box[key].setValue(float(self.sqp_config[key]))
                self.sqp_spin_box[key].valueChanged.connect(functools.partial(self.on_sqp_spin_box_value_changed, key))
                if abs(float(self.sqp_config[key])) < 1:
                    self.sqp_spin_box[key].setSingleStep(0.01)
                if float(self.sqp_config[key]) < 0:
                    self.sqp_spin_box[key].setRange(-max_sqp_config, max_sqp_config)
                if float(self.sqp_config[key]) > 100:
                    self.sqp_spin_box[key].setRange(-max_sqp_config, max_sqp_config * 1e4)
            else:
                self.sqp_config_form.addRow(self.sqp_labels[key], self.sqp_combo_box[key])
                self.sqp_combo_box[key].addItems(self.sqp_config[key])
                self.sqp_combo_box[key].currentIndexChanged.connect(
                    functools.partial(self.on_sqp_combo_box_value_changed, key))

                self.sqp_config_group_box.setLayout(self.sqp_config_form)

        self.sqp_config_scroll.setWidget(self.sqp_config_group_box)
        self.sqp_config_scroll.setWidgetResizable(True)
        self.sqp_config_scroll.setFixedHeight(400)
        self.main_hbox_layout.addWidget(self.sqp_config_scroll)

        self.robot_config_hbox.addItem(self.robot_config_form)
        self.robot_config_hbox.addStretch(1)
        self.robot_config_vbox_layout.addItem(self.robot_config_hbox)

        for key, value in list(self.robot_config.items()):
            if key != "urdf" and key != "srdf" and key != "position" and key != "orientation":
                self.robot_config_combo_box[key] = QtWidgets.QComboBox(self)
                self.robot_config_combo_box[key].addItem("Select")
                self.robot_config_form.addRow(key, self.robot_config_combo_box[key])
                self.robot_config_combo_box[key].currentIndexChanged.connect(
                    functools.partial(self.on_robot_config_combo_box_value_changed, key))
                # if type(self.robot_config[key]) is not str and type(self.robot_config[key]) is not list:
                if type(self.robot_config[key]) is not str and type(self.robot_config[key]) is not list:
                    for key1, value1 in list(self.robot_config[key].items()):
                        self.robot_config_combo_box[key].addItem(key1)
                        self.selected_robot_combo_value[key] = value1

        for key, value in list(self.robot_default_config_params.items()):
            self.robot_config_params_spin_box[key] = QtWidgets.QDoubleSpinBox(self)
            self.robot_config_form.addRow(key, self.robot_config_params_spin_box[key])
            self.robot_config_params_spin_box[key].setValue(float(value["value"]))
            self.robot_config_params_spin_box[key].valueChanged.connect(
                functools.partial(self.on_robot_spin_box_value_changed, key))
            self.robot_config_params_spin_box[key].setRange(value["min"], value["max"])
            self.robot_config_params_spin_box[key].setSingleStep(value["step"])

        self.robot_action_button_hbox.addStretch(1)

        for key in self.robot_action_buttons:
            self.robot_action_button_hbox.addWidget(self.robot_action_buttons[key])
            self.robot_action_buttons[key].clicked.connect(
                functools.partial(self.on_robot_action_button_clicked, key))
            self.robot_action_buttons[key].setMaximumWidth(220)



        self.robot_config_vbox_layout.addItem(self.robot_action_button_hbox)

        self.robot_config_vbox_layout.addStretch(1)
        self.robot_config_group_box.setLayout(self.robot_config_vbox_layout)
        self.robot_config_scroll.setWidget(self.robot_config_group_box)
        self.robot_config_scroll.setWidgetResizable(True)
        self.robot_config_scroll.setFixedHeight(400)
        self.main_hbox_layout.addWidget(self.robot_config_scroll)

    def on_robot_spin_box_value_changed(self, key, value):
        # self.selected_robot_spin_value.clear()
        self.selected_robot_spin_value[str(key)] = value

    def on_robot_action_button_clicked(self, key):
        # if not self.selected_robot_spin_value:
        for spin_box_key in self.robot_config_params_spin_box:
            self.selected_robot_spin_value[spin_box_key] = self.robot_config_params_spin_box[spin_box_key].value()

        samples = None
        duration = None
        group = None
        safe_collision_distance = None
        collision_check_distance = None
        goal_state = None
        if "samples" in self.selected_robot_spin_value:
            samples = self.selected_robot_spin_value["samples"]
        if "duration" in self.selected_robot_spin_value:
            duration = self.selected_robot_spin_value["duration"]
        if "joints_groups" in self.selected_robot_combo_value:
            group = self.selected_robot_combo_value["joints_groups"]
        if "joint_configurations" in self.selected_robot_combo_value:
            goal_state = self.selected_robot_combo_value["joint_configurations"]
        if "collision_threshold_distance" in self.selected_robot_spin_value:
            safe_collision_distance = self.selected_robot_spin_value["collision_threshold_distance"]
        if "collision_check_distance" in self.selected_robot_spin_value:
            collision_check_distance = self.selected_robot_spin_value["collision_check_distance"]

        if group is not None and goal_state is not None:
            if samples is not None and duration is not None and self.sqp_config is not None and \
                            safe_collision_distance is not None and collision_check_distance is not None:
                if key == "plan" or key == "plan_and_execute":
                    self.statusBar.clearMessage()
                    status = "Please wait, trajectory is being planned... Then trajectory will be executed.."
                    self.statusBar.showMessage(self.last_status + status)
                    status = self.initiate_plan_trajectory(group, goal_state, samples, duration,
                                                           safe_collision_distance, collision_check_distance)
                    self.statusBar.clearMessage()
                    self.statusBar.showMessage(self.last_status + status)
                if key == "plan_and_execute" or key == "execute":
                    if self.can_execute_trajectory:
                        self.statusBar.clearMessage()
                        status = "Please wait, trajectory is being executed.."
                        self.statusBar.showMessage(self.last_status + status)
                        status = self.planner.execute_trajectory()
                        self.statusBar.clearMessage()
                        self.statusBar.showMessage(self.last_status + status)
                    else:
                        self.statusBar.clearMessage()
                        status = "First plan the trajectory to execute.."
                        self.statusBar.showMessage(self.last_status + status)
        else:
            self.statusBar.clearMessage()
            status = "Please select the planning group and joint configuration.."
            self.statusBar.showMessage(self.last_status + status)

        if key == "random_pose":
            self.statusBar.clearMessage()
            status = "Please wait, random pose for the joints are being set.."
            self.statusBar.showMessage(self.last_status + status)
            if group is not None:
                status = self.planner.reset_robot_to_random_state(group)
                self.statusBar.showMessage(self.last_status + status)
            else:
                self.statusBar.clearMessage()
                status = "Please select the planning group.."
                self.statusBar.showMessage(self.last_status + status)


    def initiate_plan_trajectory(self, group, goal_state, samples, duration, collision_d_safe_limit,
                                 collision_check_distance):
        if samples is not None and duration is not None \
                and group is not None and goal_state is not None and self.sqp_config is not None:
            status, self.can_execute_trajectory = self.planner.plan_trajectory(group, goal_state, samples=int(samples),
                                                                               duration=int(duration),
                                                                               solver_config=self.sqp_config,
                                                                               collision_safe_distance=collision_d_safe_limit,
                                                                               collision_check_distance=collision_check_distance)
        else:
            status = "Please select the planning group and joint configuration.."

        return status

    def on_sqp_spin_box_value_changed(self, key, value):
        self.sqp_config[str(key)] = value
        self.sqp_yaml.save()

    def on_sqp_combo_box_value_changed(self, combo_box_key):
        # print (combo_box_key, self.sqp_combo_box[combo_box_key].currentText())
        pass

    def on_robot_config_combo_box_value_changed(self, combo_box_key):
        # self.selected_robot_combo_value.clear()
        key = self.robot_config_combo_box[combo_box_key].currentText()
        if key != "Select":
            self.selected_robot_combo_value[str(combo_box_key)] = self.robot_config[combo_box_key][str(key)]
