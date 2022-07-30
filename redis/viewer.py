import os
import json
import time
import redis
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from skimage.measure import regionprops,label
from CellCounter import get_binary_map,apply_opening,find_median_cell_size,apply_watershed

cur_path = os.path.dirname(os.path.abspath(__file__))
#获取所在文件夹
cur_path = os.path.dirname(cur_path)

client = redis.Redis(host='localhost', port=6379, db = 1)
# def str_to_bool(value):
#     if isinstance(value, bool):
#         return value
#     if value.lower() in {'false', 'f', '0', 'no', 'n'}:
#         return False
#     elif value.lower() in {'true', 't', '1', 'yes', 'y'}:
#         return True
#     raise ValueError(f'{value} is not a valid boolean value')


if __name__ == '__main__':
    print('11111111111111111')
    while True:
        if(client.scard('picture_path')) > 0:
            data = client.spop('picture_path')
            data = json.loads(data)
            # result = []
            pic_path = cur_path + '/' + data['pic_path']
            # image process
            img = plt.imread(pic_path)  

            binary_img = get_binary_map(img)
            final = label(apply_opening(binary_img))
            median_size = find_median_cell_size(final)
            cell_number = len(np.unique(final))-1
            # only apply watershed when the detected cell number is larger than 150
            if cell_number > 150: 
                final = apply_watershed(final,median_size) 

            # viewer
            points = [] 
            colors = []
            bboxes = []
            i=0
            for region in regionprops(final):
                y,x = region.centroid
                if region.area >= 2*median_size:       
                    #bound
                    minr, minc, maxr, maxc = region.bbox
                    bbox_rect = np.array([[minr, minc], [maxr, minc], [maxr, maxc], [minr, maxc]])
                    colors.append('green') #0.1)
                    bboxes.append(bbox_rect)

                elif region.area < median_size/2:
                    colors.append('red')
                else:
                    colors.append('green')

                points.append([y,x])

            points=np.array(points)
            point_properties={
                'point_colors': np.array(colors)
            }
            bboxes = np.array(bboxes)
            # print('Image name: ',image)
            print('Number of cells detected with automatic method: ', len(points))

            temp_data = {
                'cell_number': str(len(points))
            }
            client.sadd('result',json.dumps(temp_data))
        else:
            time.sleep(5)
            print('等待中')
