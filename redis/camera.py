import gxipy as gx
from PIL import Image
import os
import cv2
import json
import time
import subprocess as sp
import redis
import time
import datetime


client = redis.Redis(host='localhost', port=6379, db = 1)

cur_path = os.path.dirname(os.path.abspath(__file__))
cur_path = os.path.dirname(cur_path)

# rtspUrl = 'rtsp://10.10.211.93:8554/'

def main():
    while True:
        if (client.scard('cam_ip')) > 0:
            # create a device manager
            cam_ip = client.spop('cam_ip')
            cam_ip = json.loads(cam_ip)
            device_manager = gx.DeviceManager()
            dev_num, dev_info_list = device_manager.update_device_list()
            print(dev_num)
            if dev_num is 0:
                print("Number of enumerated devices is 0")
                return

            # 验证地址是否正确
            for dev_info in dev_info_list:
                print(str(dev_info.get('ip')))
            # open the first device
            cam = device_manager.open_device_by_ip(cam_ip['cam_ip_add'])

            # exit when the camera is a mono camera
            if cam.PixelColorFilter.is_implemented() is False:
                print("This sample does not support mono camera.")
                cam.close_device()
                return

            # set continuous acquisition
            cam.TriggerMode.set(gx.GxSwitchEntry.OFF)  #设置连续采集

            # set exposure
            cam.ExposureTime.set(5000.0)  #设置曝光时间

            # set gain
            cam.Width.set(1920)
            cam.Height.set(1080)
            cam.Gain.set(10.0)  #设置增益
            cam.stream_on()
            # 视频存储的格式
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            # 帧率
            # cam.AcquisitionFrameRate.set(360)
            fps = cam.AcquisitionFrameRate.get()
            # 视频的宽高
            size = (int(cam.Width.get() * 0.2), int(cam.Height.get() * 0.2))
            # size = (cam.Width.get(), cam.Height.get())
            sizeStr = str(size[0]) + 'x' + str(size[1])
            hz = int(1000.0/fps)
            print(cam_ip['rtsp_ip'])
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
                '-r', '20', 
                '-i', '-', # 输入
                '-b:v', '0.5M',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'ultrafast',
                '-s', sizeStr, 
                '-f', 'rtsp',# 强制输入或输出文件格式
                str(cam_ip['rtsp_ip'])]

            pipe = sp.Popen(command, stdin=sp.PIPE) #,shell=False

            while True:
                # print('11111111111111111111111111111111111111111111')
                raw_image = cam.data_stream[0].get_image()  # 使用相机采集一张图片
                if raw_image.get_status() == gx.GxFrameStatusList.INCOMPLETE:
                    continue
                rgb_image = raw_image.convert("RGB")  # 从彩色原始图像获取 RGB 图像
                # frame = cam.data_stream[0].get_image()
                numpy_image = rgb_image.get_numpy_array()
                numpy_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
                numpy_image = cv2.resize(numpy_image,(384,216),interpolation = cv2.INTER_LINEAR)
                pipe.stdin.write(numpy_image.tostring())
                # pipe.stdin.write(numpy_image)
                # out.write(numpy_image)
                # print('2222222222222222222222222222222222222222222222222')

                if (client.scard('detection')) > 0:   #添加响应
                    detection = client.spop('detection')
                    date_now = datetime.datetime.now()
                    # print(date_now)
                    print('响应检测，并向检测器发送检测信息')
                    cv2.imwrite(cur_path + "/redis/image/" + str(date_now) + '.jpg', numpy_image)
                    temp_data={"pic_path" : "/redis/image/" + str(date_now) + '.jpg',
                        }
                    client.sadd("picture_path",json.dumps(temp_data))
                    time.sleep(5)

                # if (client.scard('location')) > 0:   #添加响应
                #     location = client.spop('location')
                #     location = json.loads(location)
                #     date_now = datetime.datetime.now()
                #     # print(date_now)
                #     print('响应标注，截取当前图片并保存相应的json')
                #     cv2.imwrite(cur_path + "/redis/data/image/" + str(date_now) + '.jpg', numpy_image)
                #     print('保存图片成功')
                #     jsontext = {'points':[]}
                #     width_1st = 720 * int(location['width_1st'])
                #     height_1st = 360 * int(location['height_1st'])
                #     width_3rd = 720 * int(location['width_3rd'])
                #     height_3rd = 360 * int(location['height_3rd'])

                #     jsontext['points'].append({str(width_1st),str(height_1st)})
                #     jsontext['points'].append({str(width_3rd),str(height_3rd)})
                #     jsondata = json.dumps(jsontext,indent=4,separators=(',', ': '))
                #     json_path = cur_path + "/redis/data/image/" + str(date_now) + '.json'
                #     f = open(json_path, 'w')

                #     f.write(jsondata)
                #     f.close()
                #     print('保存json成功')

                if cv2.waitKey(1) & 0xFF == 27:
                    break
                # cv2.waitKey(100)

            # stop data acquisition
            cam.stream_off()

            # close device
            cam.close_device()

if __name__ == "__main__":
    main()

