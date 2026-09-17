# lane_driving

`lane_driving` 是一个基于 ROS 2 的车道线跟随功能包。节点订阅相机图像，检测车道线，并向 `/controller/cmd_vel` 发布速度指令。

## 依赖

本功能包需要在完整的 ROS 2 小车工程中运行，主要依赖：

- `rclpy`
- `geometry_msgs`
- `sensor_msgs`
- `cv_bridge`
- `sdk.pid`
- `sdk.common`
- `example.self_driving.lane_detect`
- `peripherals`
- `controller`

其中 `sdk`、`example`、`peripherals` 和 `controller` 不包含在本仓库中，请先准备对应的完整工程。

## 放置功能包

将仓库放到 ROS 2 工作空间的 `src` 目录：

```bash
cd ~/ros2_ws/src
git clone https://github.com/Zhuqiben/lane_driving.git
```

目录结构应类似：

```text
ros2_ws/
└── src/
    └── lane_driving/
        ├── lane_driving/
        ├── resource/
        ├── test/
        ├── package.xml
        ├── setup.py
        └── setup.cfg
```

## 编译

在工作空间根目录执行：

```bash
source /opt/ros/<ros2-distribution>/setup.bash
cd ~/ros2_ws
colcon build --packages-select lane_driving
source install/setup.bash
```

每次打开新终端，都需要重新加载 ROS 2 和工作空间环境：

```bash
source /opt/ros/<ros2-distribution>/setup.bash
source ~/ros2_ws/install/setup.bash
```

## 启动

编译安装后，设置 `need_compile=True`，通过 ROS 2 包索引查找依赖功能包：

```bash
export need_compile=True
ros2 launch lane_driving lane_driving.launch.py
```

也可以覆盖相机话题和启动状态：

```bash
ros2 launch lane_driving lane_driving.launch.py \
  camera_topic:=depth_cam/rgb0/image_raw \
  start:=true
```

默认参数：

```text
camera_topic: depth_cam/rgb0/image_raw
start: true
```

当 `need_compile` 不是 `True` 时，启动文件会使用源码模式下预设的依赖路径：

```text
/home/ubuntu/ros2_ws/src/peripherals
/home/ubuntu/ros2_ws/src/driver/controller
```

如果实际工作空间路径不同，请先调整 `lane_driving/lane_driving.launch.py`。

## 运行检查

```bash
ros2 node list
ros2 topic list
ros2 topic echo /controller/cmd_vel
ros2 service list
```

节点会发布调试图像到私有话题 `~/image_result`，并提供退出服务：

```bash
ros2 service call /lane_driving_node/exit std_srvs/srv/Trigger "{}"
```

退出时节点会发布零速度指令。

## 常见问题

### 找不到 `peripherals` 或 `controller`

确认对应功能包已经放入同一个工作空间并成功编译：

```bash
ros2 pkg prefix peripherals
ros2 pkg prefix controller
```

### 找不到 `sdk` 或 `example`

确认完整工程已经提供这些 Python 模块，并检查当前终端是否可以导入：

```bash
python3 -c "import sdk; import example.self_driving"
```

### 没有图像或速度输出

检查相机话题和速度话题：

```bash
ros2 topic list | grep image
ros2 topic echo /controller/cmd_vel
```

确认相机、控制器和 `lane_driving` 节点均已启动，且 `camera_topic` 与实际图像话题一致。
