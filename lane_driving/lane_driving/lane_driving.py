#!/usr/bin/env python3
# encoding: utf-8
# 车道线跟随 - 精简版 (保留 camera_topic 参数)

import os
import cv2
import time
import queue
import rclpy
import threading
import numpy as np
import sdk.pid as pid
from rclpy.node import Node
import sdk.common as common
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from std_srvs.srv import Trigger
from example.self_driving import lane_detect
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup


class SelfDrivingNode(Node):
    def __init__(self, name):
        rclpy.init()
        super().__init__(name, allow_undeclared_parameters=True,
                         automatically_declare_parameters_from_overrides=True)
        self.name = name
        self.is_running = True
        self.pid = pid.PID(0.005, 0.0, 0.0)

        self.machine_type = os.environ.get('MACHINE_TYPE', '')
        self.lane_detect = lane_detect.LaneDetector("yellow")

        # ===== 从参数服务器读取配置 =====
        self.start = self.get_parameter('start').value if self.has_parameter('start') else True
        self.camera_topic = self.get_parameter('camera_topic').value if self.has_parameter(
            'camera_topic') else 'depth_cam/rgb0/image_raw'
        # ================================

        # 速度参数
        self.normal_speed = 0.2

        # 状态变量
        self.image_queue = queue.Queue(maxsize=2)
        self.bridge = CvBridge()
        self.lock = threading.RLock()

        # 发布器
        self.cmd_vel_topic = '/controller/cmd_vel'
        self.mecanum_pub = self.create_publisher(Twist, self.cmd_vel_topic, 1)
        self.result_publisher = self.create_publisher(Image, '~/image_result', 1)

        # 服务
        self.create_service(Trigger, '~/exit', self.exit_srv_callback)

        # ===== 使用 camera_topic 订阅图像 =====
        self.get_logger().info(f'Subscribing to camera topic: {self.camera_topic}')
        self.image_sub = self.create_subscription(
            Image, self.camera_topic, self.image_callback, 1)
        # ======================================

        # 等待服务
        timer_cb_group = ReentrantCallbackGroup()
        self.client = self.create_client(Trigger, '/controller_manager/init_finish')
        self.client.wait_for_service()

        self.timer = self.create_timer(0.0, self.init_process, callback_group=timer_cb_group)

        self.get_logger().info('\033[1;32mSelf Driving Node Started\033[0m')
        self.get_logger().info(f'Camera Topic: {self.camera_topic}')

    def init_process(self):
        self.timer.cancel()
        self.get_logger().info('\033[1;32mStarting lane following...\033[0m')
        threading.Thread(target=self.main, daemon=True).start()

    def image_callback(self, ros_image):
        cv_image = self.bridge.imgmsg_to_cv2(ros_image, "rgb8")
        rgb_image = np.array(cv_image, dtype=np.uint8)
        if self.image_queue.full():
            self.image_queue.get()
        self.image_queue.put(rgb_image)

    def exit_srv_callback(self, request, response):
        self.get_logger().info('\033[1;32mSelf driving exit\033[0m')
        self.mecanum_pub.publish(Twist())
        self.is_running = False
        response.success = True
        response.message = "exit"
        return response

    def main(self):
        while self.is_running and rclpy.ok():
            time_start = time.time()

            try:
                image = self.image_queue.get(block=True, timeout=1)
            except queue.Empty:
                if not self.is_running:
                    break
                continue

            if self.start and image is not None:
                h, w = image.shape[:2]

                # 获取车道线二值图
                binary_image = self.lane_detect.get_binary(image)

                # 车道线检测
                result_image, lane_angle, lane_x, max_area = self.lane_detect(binary_image, image.copy())

                # PID控制转向
                twist = Twist()
                twist.linear.x = self.normal_speed

                # 计算转向角度
                self.pid.SetPoint = 90  # 目标车道中心
                if abs(lane_x - 90) < 20:
                    lane_x = 90
                self.pid.update(lane_x)
                twist.angular.z = common.set_range(self.pid.output, -0.8, 0.8)

                # 速度限制
                if twist.linear.x <= 0:
                    twist.linear.x = self.normal_speed
                else:
                    twist.linear.x = min(twist.linear.x, self.normal_speed)

                self.mecanum_pub.publish(twist)

                # 发布结果图像（用于调试）
                bgr_image = cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR)
                self.result_publisher.publish(self.bridge.cv2_to_imgmsg(bgr_image, "bgr8"))

                # 显示图像
                cv2.imshow('Lane Following', bgr_image)
                if cv2.waitKey(1) == ord('q'):
                    self.is_running = False
                    break

            else:
                time.sleep(0.01)

            # 控制循环频率
            time_d = 0.03 - (time.time() - time_start)
            if time_d > 0:
                time.sleep(time_d)

        self.mecanum_pub.publish(Twist())
        cv2.destroyAllWindows()
        rclpy.shutdown()


def main():
    node = SelfDrivingNode('lane_driving_node')
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        node.destroy_node()


if __name__ == "__main__":
    main()