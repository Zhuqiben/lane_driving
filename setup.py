from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'lane_driving'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # ★ 关键：将 launch 文件安装到 share 目录 ★
        (os.path.join('share', package_name, 'launch'),
            glob('lane_driving/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='ubuntu@todo.todo',
    description='Lane driving',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'lane_driving = lane_driving.lane_driving:main',
        ],
    },
)