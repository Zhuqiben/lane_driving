# lane_driving 部署说明

## 1. 功能包简介

`lane_driving` 是一个基于 ROS 2 的车道线跟随功能包。节点订阅相机图像，进行车道线检测，并向底盘控制器发布速度指令。

当前实现依赖工作空间中的其他模块，不能脱离完整的 ROS 2 工程单独运行：

- `rclpy`
- `std_msgs`
- `geometry_msgs`
- `sensor_msgs`
- `cv_bridge`
- `sdk.pid`
- `sdk.common`
- `example.self_driving.lane_detect`
- `peripherals` 功能包
- `controller` 功能包

其中 `sdk`、`example`、`peripherals` 和 `controller` 的具体来源应以目标设备或完整工程提供的版本为准。

## 2. 放置功能包

将本仓库放置到 ROS 2 工作空间的 `src` 目录：

```bash
cd ~/ros2_ws/src
git clone https://github.com/Zhuqiben/lane_driving.git
```

如果已经下载本仓库，则确认目录结构类似：

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

## 3. 准备依赖

确认 ROS 2 环境已经加载，并确保以下依赖可以被当前环境发现：

```bash
source /opt/ros/<ros2-distribution>/setup.bash
```

如果依赖功能包位于同一个工作空间，请将它们一并放在 `src` 目录中。`lane_driving.launch.py` 会启动：

- `peripherals` 中的 `launch/depth_camera.launch.py`
- `controller` 中的 `launch/controller.launch.py`

节点源码还会导入 `sdk` 和 `example.self_driving`，请先按照完整工程的部署方式安装或配置这些 Python 模块。

## 4. 编译功能包

在工作空间根目录执行：

```bash
cd ~/ros2_ws
colcon build --packages-select lane_driving
```

编译完成后加载工作空间：

```bash
source install/setup.bash
```

每次打开新的终端，都需要重新加载 ROS 2 和工作空间环境：

```bash
source /opt/ros/<ros2-distribution>/setup.bash
source ~/ros2_ws/install/setup.bash
```

## 5. 启动方式

### 5.1 使用 launch 文件

当前 launch 文件会根据 `need_compile` 环境变量选择依赖功能包路径：

- `need_compile=True`：通过 ROS 2 包索引查找 `peripherals` 和 `controller`；
- 其他值：使用源码工作空间中的固定路径。

编译安装后，推荐使用：

```bash
export need_compile=True
ros2 launch lane_driving lane_driving.launch.py
```

### 5.2 配置参数

可以覆盖默认相机话题和启动状态：

```bash
ros2 launch lane_driving lane_driving.launch.py \
  camera_topic:=depth_cam/rgb0/image_raw \
  start:=true
```

默认参数为：

```text
camera_topic: depth_cam/rgb0/image_raw
start: true
```

## 6. 运行检查

启动后可以检查节点、话题和服务：

```bash
ros2 node list
ros2 topic list
ros2 topic echo /controller/cmd_vel
ros2 service list
```

节点会发布调试图像到私有话题 `~/image_result`，并向 `/controller/cmd_vel` 发布底盘速度指令。

## 7. 停止运行

可以使用终端中的 `Ctrl+C` 停止 launch。节点也提供退出服务：

```bash
ros2 service call /lane_driving_node/exit std_srvs/srv/Trigger "{}"
```

退出处理会发布零速度指令，然后停止图像处理循环。

## 8. 常见问题

### 找不到 `peripherals` 或 `controller`

确认对应功能包已经放入工作空间并成功编译，然后检查：

```bash
ros2 pkg prefix peripherals
ros2 pkg prefix controller
```

如果使用源码路径模式，请检查 `lane_driving.launch.py` 中的路径是否与目标工作空间一致。

### 找不到 `sdk` 或 `example`

这些模块不是本功能包目录中的文件。请确认完整工程已经提供它们，并且当前终端的 Python 环境可以导入：

```bash
python3 -c "import sdk; import example.self_driving"
```

### 没有图像或没有速度输出

检查相机话题是否存在，并确认启动参数与实际话题一致：

```bash
ros2 topic list | grep image
ros2 topic echo /controller/cmd_vel
```

同时确认相机、控制器和 `lane_driving` 节点均已启动。
