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

import sys
from Processor import Processor
from classes import coco


if __name__ == "__main__":

    pic_height = 2560
    pic_width = 1920

    client = redis.Redis(host='localhost', port=6379, db = 1)
    processor = Processor('ki67.trt')
    print("模型加载完毕")

    while True:
        try:
            if client.llen("detection_queue") > 0:
                pic_path = client.lpop("detection_queue")
                _image = np.array(Image.open(pic_path))
                output = processor.detect(_image) 
                boxes, confs, classes = processor.post_process(output)
                results = {"response":[]}
                for box, conf, cls in zip(boxes, confs, classes):
                    xmin, ymin, xmax, ymax = box
                    conf = conf[0]
                    label = coco[cls]
                    (xmin,ymin) = (float(xmin)/(pic_height * 0.25), float(ymin)/(pic_width * 0.25))
                    (xmax,ymax) = (float(xmax)/(pic_height * 0.25), float(ymax)/(pic_width * 0.25))
                    point_dict = {'rectangle': {'first': {'x': xmin, 'y': ymin}, 'second': {'x': xmax, 'y': ymax}}, 'label': str(label)}
                    results["response"].append(point_dict)
                client.rpush("detection_result", json.dumps(results))
        except Exception as e:
            print(e)
