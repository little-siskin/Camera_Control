import gxipy as gx
from PIL import Image
import os
import cv2
import json
import time
import subprocess as sp
import redis
import time
import threading
import datetime
import numpy as np
import re


from Processor import Processor
# from Visualizer import Visualizer
# from elements.yolo import OBJ_DETECTION
from classes import coco


client = redis.Redis(host='localhost', port=6379, db = 1)

#获取所在文件夹               获取当前脚本的完整路径
cur_path = os.path.dirname(os.path.abspath(__file__))
#获取所在文件夹
cur_path = os.path.dirname(cur_path)

pic_height = 2560
pic_width = 1920

pic_dict = {}
# 注意图像的宽高
image = np.zeros((int(pic_height * 0.25), int(pic_width * 0.25), 3), np.uint8)

def location(date_now, numpy_image, location):  # 截图并保存标注   目前保存yolo标注&ki67
    print('响应标注，截取当前图片并保存相应的json')
    with open("/home/o/Camera_Control/demo.json", "r") as fp:
        data = json.load(fp)
        new_data = data
    cv2.imwrite(cur_path + "/redis/data/image/" + str(date_now) + '.jpg', numpy_image)
    print('保存图片成功')
    #-----------------------------------
    pattern = re.compile(r'\[\(.*?\),\(.*?\),type:\w_\d\]')
    # allRect = pattern.findall(location.decode())
    allRect = pattern.findall(location)
    pos = re.compile(r'\(.*?\)')
    statep = re.compile(r'type:\w_\d')
    # content = []
    for rect in allRect:
        # width_1st, height_1st = rect[rect.find('(')+1:rect.find(')')].split(',')
        # width_3rd, height_3rd = rect[rect.find(')')+3:rect.find('type:')-2].split(',')
        # print(rect)
        allpos = pos.findall(rect)
        # print(allpos)
        width_1st, height_1st = allpos[0][1:-1].split(',')
        width_3rd, height_3rd = allpos[1][1:-1].split(',')
        state = statep.findall(rect)
        state = state[0][state[0].find(':')+1]
        
        width_1st = str(pic_height * float(width_1st))
        height_1st = str(pic_width * float(height_1st))
        width_3rd = str(pic_height * float(width_3rd))
        height_3rd = str(pic_width * float(height_3rd))

        # print(width_1st)
        # point = [[width_1st.tolist(), height_1st.tolist()], [width_3rd.tolist(), height_3rd.tolist()]]
        point = [[width_1st, height_1st], [width_3rd, height_3rd]]
        # print(point)
        item_dict = {'label':state, 'line_color':None,'fill_color':None, 'points':point,"shape_type": "rectangle","flags": {}}
        new_data['shapes'].append(item_dict)
    json_path = cur_path + "/redis/data/json/" + str(date_now) + '.json'
    # f = open(json_path, 'w')

    new_data['imagePath'] = cur_path + "/redis/data/image/" + str(date_now) + '.jpg'
    new_data["imageData"] = None
    new_data["imageHeight"] = pic_height
    new_data["imageWidth"] = pic_width
    with open(json_path, 'w') as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
        print('保存json成功')
    # f.write(jsondata)
    # f.close()
    print('标注流程完成')
    # return

if __name__ == "__main__":
    processor = Processor('ki67.trt')
    print("模型加载完毕")
    while True:
        if (client.scard('detections')) > 0:
            print("------------------------")
            detections = client.spop('detections')
            detections = json.loads(detections)
            rtsp_ip = detections['rtsp_ip']
            print(rtsp_ip)
            results = []
            print('开始检测')
            # global image
            # _image = image.copy()
            # cam_ip = json.loads(cam_ip)'
            _image = np.copy(pic_dict[str(rtsp_ip)])
            output = processor.detect(_image) 
            boxes, confs, classes = processor.post_process(output)
            for box, conf, cls in zip(boxes, confs, classes):
                xmin, ymin, xmax, ymax = box
                conf = conf[0]
                label = coco[cls]
                # score = obj['score']
                # [(xmin,ymin),(xmax,ymax)] = obj['bbox']
                (xmin,ymin) = (float(xmin)/(pic_height * 0.25), float(ymin)/(pic_width * 0.25))
                (xmax,ymax) = (float(xmax)/(pic_height * 0.25), float(ymax)/(pic_width * 0.25))
                result = 'point_1:' + str((xmin,ymin)) + ' point_3:' + str((xmax,ymax)) + ' label:' + str(label)
                results.append(result)
            print(results)
            temp_data={
                "results" : results,
            }
            client.sadd("result" + "_" + str(rtsp_ip),json.dumps(temp_data))
        elif (client.scard('cam_ip')) > 0:
            # create a device manager
            cam_ip = client.spop('cam_ip')
            cam_ip = json.loads(cam_ip)
            print(cam_ip['cam_ip_add'])
            cam = get_dev(cam_ip['cam_ip_add'])
            # cam = cam_set(cam)
            pipe = pipe_set(cam, cam_ip['rtsp_ip'])
            
            t1 = threading.Thread(target=pull_push_img, args=(cam,pipe,cam_ip['rtsp_ip']))
            t1.start()
        else:
            continue



