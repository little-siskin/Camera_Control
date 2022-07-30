from multiprocessing import Process, Queue
from app01.models import User, Cam
import subprocess
import gxipy as gx
import cv2
import datetime
import numpy as np
import os
import time
import signal

WIDTH, HEIGHT = 2560, 1920

class CameraManage:
    """摄像头管理"""
    device_manager = gx.DeviceManager()
    dev_num, dev_info_list = device_manager.update_device_list()
    # key, value(pid: 进程pid, camera: Camera实例)
    ip_pid = {}
    rtspip_pid = {}
    ip_camera = {}

    def __init__(self):
        pass

    @classmethod
    def getCameraByIp(cls, camera_ip, pic_height=2560, pic_width=1920):
        for item in cls.dev_info_list:
            if item["ip"] == camera_ip:
                return True
        return False

    @classmethod
    def startPushStream(cls, queue, camera_ip, rtsp_ip):
        try:
            camera_ip, rtsp_ip = queue.get(True)
            camera = cls.device_manager.open_device_by_ip(camera_ip)
            if not camera.PixelColorFilter.is_implemented():
                print("This sample does not support mono cameraera.")
                camera.close_device()
                return None, None

            camera.TriggerMode.set(gx.GxSwitchEntry.OFF)  #设置连续采集
            camera.ExposureTime.set(5000.0)  #设置曝光时间
            camera.Width.set(WIDTH)
            camera.Height.set(HEIGHT)
            camera.Gain.set(10.0)  #设置增益
            camera.stream_on()

            pid = os.getpid()
            cls.ip_pid[camera_ip] = pid
            cls.rtspip_pid[rtsp_ip] = pid
            print(len(cls.rtspip_pid))
            cls.ip_camera[camera_ip] = camera 

            fps = camera.AcquisitionFrameRate.get()
            size = (int(camera.Width.get() * 0.25), int(camera.Height.get() * 0.25))
            sizeStr = f'{size[0]}x{size[1]}'
            hz = int(1000.0/fps)

            command = [
                'ffmpeg',
                # '-vf','scale=640:360',
                # 're',#
                # '-y', # 无需询问即可覆盖输出文件
                '-f', 'rawvideo', # 强制输入或输出文件格式
                '-vcodec','rawvideo', # 设置视频编解码器。这是-codec:v的别名rawvideo
                '-pix_fmt', 'bgr24', # 设置像素格式
                '-s', sizeStr, # 设置图像大
                # '-r', str(fps), # 设置帧率
                '-r', '30', 
                '-i', '-', # 输入
                '-b:v', '1500k',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset:v', 'ultrafast', # 编码速度最快
                '-s', sizeStr, 
                '-max_delay', '100',
                '-tune:v', 'zerolatency', # 实时推流 0延迟
                # '-fflags', 'nobuffer', #无缓存
                # '-profile:v', 'baseline',  # 待检测
                '-start_time_realtime','0',
                # '-rtsp_transport', 'tcp',
                '-g', '5',
                '-f', 'rtsp',# 强制输入或输出文件格式
                '-loglevel', 'quiet',
                rtsp_ip]

            pipe = subprocess.Popen(command, stdin=subprocess.PIPE) #,shell=False

            while True:
                print("pushing")
                raw_image = camera.data_stream[0].get_image() 
                if not raw_image or raw_image.get_status() == gx.GxFrameStatusList.INCOMPLETE:
                    continue
                rgb_image = raw_image.convert("RGB")
                numpy_image = rgb_image.get_numpy_array()
                numpy_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
                numpy_image = cv2.resize(numpy_image,(int(HEIGHT* 0.25),int(WIDTH * 0.25)),interpolation = cv2.INTER_LINEAR)
                pipe.stdin.write(numpy_image.tostring())

        except Exception as e:
            print("Exception: ", e)
            time.sleep(1)
            if 'pipe' in dir():
                pipe.stdin.close()
                del pipe
            return camera_ip, rtsp_ip

        pipe.stdin.close()
        del pipe
        return camera_ip, rtsp_ip

    @classmethod
    def closeCamera(cls, camera_ip="", rtsp_ip=""):
        """
        释放摄像头,解决摄像头重复获取?
        """
        if camera_ip and rtsp_ip:
            print("closeCamera")
            camera = cls.ip_camera[camera_ip] 
            camera.stream_off()
            camera.close_device()
            del cls.ip_camera[camera_ip]
            del cls.ip_pid[camera_ip]
            del cls.rtspip_pid[rtsp_ip]

    @classmethod
    def error(cls, e):
        print("Error: ", e)

    @classmethod
    def stopPushingStream(cls, queue):
        try:
            rtsp_ip = queue.get(True)
            pid = cls.rtspip_pid[rtsp_ip]
            os.kill(pid, signal.SIGINT)
        except Exception as e:
            print("stopPushingStream: ", e) 
