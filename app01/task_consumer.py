import os
import re
import sys, errno
import signal
# from signal import signal, SIGPIPE, SIG_DFL
# signal(SIGPIPE, SIG_DFL)
import gxipy as gx
import cv2
import numpy as np
import datetime
import time
import collections
import multiprocessing 
import subprocess
import threading
from django.http import HttpResponse
import json

Msg = collections.namedtuple("Msg", ["event", "args"])

class BaseProcess(multiprocessing.Process):
    """任务监视进程"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = multiprocessing.Manager().Queue()

    def send(self, event, *args):
        """Msg(*args)"""
        msg = Msg(event, args)
        self.queue.put(msg)

    def dispatch(self, msg):
        """未实现异常管理"""
        event, args = msg

        handler = getattr(self, f"do_{event}")
        if not handler:
            raise NotImplementedError()

        if event == "startPushingStream":
            t = threading.Thread(target=handler)
            sys.stdout.flush()
            print("startPushingStream")
            t.start()
        else:
            handler(*args)

    def run(self):
        while True:
            if not self.queue.empty():
                msg = self.queue.get()
                self.dispatch(msg)

device_manager = gx.DeviceManager()
WIDTH, HEIGHT = 2560, 1920

class Task(BaseProcess):
    def __init__(self, camera_ip, rtsp_ip):
        super(Task, self).__init__()
        self.stopPushing = False
        self.tagging = False
        self.save_cur_pic = False
        self.save_pic_path = ""
        self.camera_ip = camera_ip
        self.rtsp_ip = rtsp_ip

    def do_startPushingStream(self):
        try:
            camera = device_manager.open_device_by_ip(self.camera_ip)
            if not camera.PixelColorFilter.is_implemented():
                camera.close_device()
                return

            camera.TriggerMode.set(gx.GxSwitchEntry.OFF)  #设置连续采集
            camera.ExposureTime.set(5000.0)  #设置曝光时间
            camera.Width.set(WIDTH)
            camera.Height.set(HEIGHT)
            camera.Gain.set(10.0)  #设置增益
            camera.stream_on()
            
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
                '-f', 'rtsp', # 强制输入或输出文件格式
                '-loglevel', 'quiet',
                self.rtsp_ip,
            ]
            pipe = subprocess.Popen(command, stdin=subprocess.PIPE) #,shell=False

            # while not self.stopPushingEvent.is_set():
            while not getattr(self, "stopPushing"):

                raw_image = camera.data_stream[0].get_image() 
                if not raw_image or raw_image.get_status() == gx.GxFrameStatusList.INCOMPLETE:
                    continue
                rgb_image = raw_image.convert("RGB")
                numpy_image = rgb_image.get_numpy_array()
                numpy_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
                numpy_image = cv2.resize(numpy_image,(int(WIDTH* 0.25),int(HEIGHT* 0.25)),interpolation = cv2.INTER_LINEAR)

                # save current image to tag or detect
                if getattr(self, "save_cur_pic"):
                    dirname = os.path.dirname(getattr(self, 'save_pic_path'))
                    if not os.path.exists(dirname):
                        os.mkdir(dirname)
                    assert os.path.exists(dirname)
                    cv2.imwrite(f"{getattr(self, 'save_pic_path')}", numpy_image)
                    setattr(self, "save_cur_pic", False)
                pipe.stdin.write(numpy_image.tostring())

            print("camera close_device")
            time.sleep(1)
            pipe.stdin.close()
            # change 结束推流进程
            pipe.terminate()
            camera.stream_off()
            camera.close_device()
        except IOError as e:
            # Broken pipe error 
            # 上游 python 发送数据，下游不需要数据，发送SIGPIPE给上游进程
            if e.errno == errno.EPIPE:
                print("EPIPE")
        except Exception as e:
            print("PushingStream __run__: ", e)
            if "camera" in locals():
                print("camera close_device")
                time.sleep(1)
                # change
                pipe.stdin.close()
                pipe.terminate()
                camera.stream_off()
                camera.close_device()

    def do_stopPushingStream(self):
        self.stopPushing = True
        
    def do_tagging(self, path):
        setattr(self, "save_cur_pic", True)
        setattr(self, "save_pic_path", path)

    def do_detection(self, path):
        setattr(self, "save_cur_pic", True)
        setattr(self, "save_pic_path", path)

    def __str__(self):
        return f"Camera({self.camera_ip}) pushing on {self.rtsp_ip}"











# import sys
# sys.path.append("/home/o/Camera_Control_multiprocess/redis")
# from Processor import *

# class Inference(BaseProcess):
# 
#     _inferenceCls = Processor('ki67.trt')
# 
#     def __init__(self):
#         super(Inference, self).__init__()
# 
#     def do_detection(self, _inferenceCls, pipe, picPath):
#         try:
#             _image = cv2.imread(picPath)
#             output = Inference._inferenceCls.detect(_image) 
#             boxes, confs, classes = Inference._inferenceCls.post_process(output)
# 
#             results = {'response': []}
#             for box, conf, cls in zip(boxes, confs, classes):
#                 xmin, ymin, xmax, ymax = box
#                 conf = conf[0]
#                 label = coco[cls]
#                 # score = obj['score']
#                 # [(xmin,ymin),(xmax,ymax)] = obj['bbox']
#                 (xmin,ymin) = (float(xmin)/(pic_height * 0.25), float(ymin)/(pic_width * 0.25))
#                 (xmax,ymax) = (float(xmax)/(pic_height * 0.25), float(ymax)/(pic_width * 0.25))
#                 point_dict = {'rectangle': {'first': {'x': xmin, 'y': ymin}, 'second': {'x': xmax, 'y': ymax}}, 'label': str(label)}
#                 results['response'].append(point_dict)
# 
#             pipe.send(json.dumps(results))
#             pipe.close()
#         except Exception as e:
#             print(e)
#             pipe.send(e)
#             pipe.close()

        
