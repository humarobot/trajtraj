需要下载 iai_bots, https://github.com/code-iai/iai_robots.git
用rosrun xacro xacro iai_donbot.urdf.xacro > don_bot.urdf 生成一个urdf文件
把config/robot_config_don_bot.yaml前两行改了，改成刚生成的urdf路径

requirements:
pyside6
cvxpy
yamlordereddictloader
srdfdom 需要下载编译
等等