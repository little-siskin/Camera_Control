from unittest import result
from django.db.models.fields import NOT_PROVIDED
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.shortcuts import redirect
from django.http import HttpResponse,JsonResponse
from django import forms
from django.contrib import messages
from app01.models import User, Cam
from functools import wraps
from django.urls import reverse
from django.contrib.auth.decorators import login_required

import os
import re
import redis
import json
import time
import datetime
import functools
import ctypes
import signal
import gxipy as gx
import multiprocessing
from multiprocessing import Process, Queue, Manager
from app01.task_consumer import *

import sys

client = redis.Redis(host='localhost', port=6379, db = 1)

ALLPROCESS = {}

WIDTH, HEIGHT = 2560, 1920

def check_login(f):
    """
    装饰器登录状态检测
    """
    @functools.wraps(f)
    def inner(request,*arg,**kwargs):
        if request.session.get('is_login')=='1':
            return f(request,*arg,**kwargs)
        else:
            return redirect('/logins')
    return inner

# 尚未完成
class UserForm(forms.Form):
    user_name = forms.CharField(label='用户名',max_length=30)
    email = forms.EmailField(label='邮箱',max_length=30)
    pwd = forms.CharField(label='密码',widget=forms.PasswordInput(),max_length=30)
    authority = forms.CharField(label='权限', max_length = 2)
    cam_id = forms.IntegerField(label='摄像头id')

def regist(request):
    if request.method == 'POST':
        userform = UserForm(request.POST)
        if userform.is_valid():
            user_name = userform.cleaned_data['user_name']
            pwd = userform.cleaned_data['pwd']
            email = userform.cleaned_data['email']
            authority = userform.cleaned_data['authority']
            try:
                cam_id = userform.cleaned_data['cam_id']
                cam_instance = Cam.objects.get(id = cam_id)
            except:
                error_message = "摄像头id未找到,请重新输入。"
                context = {
                    "error_message":error_message,
                    "userform":userform,
                }
                return render(request, "regist.html", context)
            # user = User()
            if(User.objects.filter(user_name=user_name)):
                error_message = "用户名重复"
                context = {
                    "error_message":error_message,
                    "userform":userform,
                }
                return render(request, "regist.html", context)
            user = User.objects.create(user_name = user_name,pwd = pwd,email = email,authority = authority,cam_id = cam_instance)
            user.save()

            return HttpResponse('regist success!!!')
    else:
        userform = UserForm()
    return render(request, 'regist.html',{'userform':userform})




# 2022.05.06 wt
def login(request):
    """
    手机登录
    """
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('pwd').strip()

        if username and password:
            user = User.objects.filter(user_name=username, pwd=password)
            if len(user) > 0:
                try:
                    cam_ip = user[0].cam_id.cam_ip
                    rtsp_ip = user[0].cam_id.rtsp_ip

                    # Python 不能传递非 ctype(camera) 参数 
                    _, dev_info_list = device_manager.update_device_list()
                    if not len(dev_info_list):
                        return HttpResponse("camera not online", status="400")
                    camera_ip_list = [info["ip"] for info in dev_info_list]
                    if not cam_ip in camera_ip_list:
                        return HttpResponse("Illegal camera ip", status="400")
                    if rtsp_ip in ALLPROCESS.keys():
                        return HttpResponse(rtsp_ip)

                    process = Task(cam_ip, rtsp_ip)
                    ALLPROCESS[rtsp_ip] = process
                    process.start()
                    process.send("startPushingStream")

                    return HttpResponse(rtsp_ip)
                except Exception as e:
                    print(e)
                    return HttpResponse()
            else:
                # username or password error
                return HttpResponse(status="400")
        else:
            return HttpResponse()

def stoppushing(request):
    """
    停止推流
    """
    if request.method == 'POST':
        rtsp_ip = request.POST.get('rtsp_ip')  
        process = ALLPROCESS[rtsp_ip] if rtsp_ip in ALLPROCESS.keys() else None
        if not process:
            return HttpResponse("camera not online", status="400")

        process = ALLPROCESS[rtsp_ip]
        process.send("stopPushingStream")
        time.sleep(1)
        # change
        ALLPROCESS[rtsp_ip].terminate()
        del ALLPROCESS[rtsp_ip]
        return HttpResponse("finish")
    else:
        print("stoppushing get")
        return HttpResponse("rtsp ip is empty", status="400")


def detection(request):
    if request.method == "POST":
        try:
            rtsp_ip = request.POST.get('rtsp_ip')
            # 测试
            # client.rpush("detection_queue", "./test.png")
            # while not client.llen("detection_result") > 0:
            #     pass
            # result = client.lpop("detection_result")
            # return HttpResponse(result)
            process = ALLPROCESS[rtsp_ip] if rtsp_ip in ALLPROCESS.keys() else None
            if not process:
                return HttpResponse("camera not online", status="400")

            # 保存对应摄像头下的图片 
            rtspip_format = re.split(':|\/|\.', rtsp_ip)
            current_path = os.path.abspath(__file__) # app01/views.py
            father_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + "..") # app01/
            needed_path = os.path.join(father_path, "Detection")
            if not os.path.exists(needed_path):
                os.mkdir(needed_path)

            save_path = f"{needed_path}/{'_'.join(filter(lambda x: x != '', rtspip_format)) + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
            pic_save_path = save_path + ".jpg"
            process.send("detection", pic_save_path)

            time.sleep(1) 
            client.rpush("detection_queue", pic_save_path)
            while not client.llen("detection_result") > 0:
                pass
            result = client.lpop("detection_result")
            return HttpResponse(result)
        except Exception as e:
            print(e)
            return HttpResponse("FAIL", status="400")

def tagging(request):
    if request.method == "POST":
        try:
            relativePos = request.POST.get("relativePos")
            rtsp_ip = request.POST.get("rtsp_ip")
            process = ALLPROCESS[rtsp_ip] if rtsp_ip in ALLPROCESS.keys() else None
            if not process:
                return HttpResponse("camera not online", status="400")

            # 保存对应摄像头下的图片 
            rtspip_format = re.split(':|\/|\.', rtsp_ip)
            current_path = os.path.abspath(__file__) # app01/views.py
            father_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + "..") # app01/
            needed_path = os.path.join(father_path, "Tagging")
            if not os.path.exists(needed_path):
                os.mkdir(needed_path)

            save_path = f"{needed_path}/{'_'.join(filter(lambda x: x != '', rtspip_format)) + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
            pic_save_path = save_path + ".jpg"
            json_path = save_path + ".json"
            process.send("tagging", pic_save_path)

            time.sleep(1)
            pattern = re.compile(r'\[\(.*?\),\(.*?\),type:\w_\d\]')
            allRect = pattern.findall(relativePos)
            pos = re.compile(r'\(.*?\)')
            statep = re.compile(r'type:\w_\d')

            new_data = {"shapes": []}
            for rect in allRect:
                allpos = pos.findall(rect)
                width_1st, height_1st = allpos[0][1:-1].split(',')
                width_3rd, height_3rd = allpos[1][1:-1].split(',')
                state = statep.findall(rect)
                state = state[0][state[0].find(':')+1]
                
                width_1st = str(HEIGHT * float(width_1st))
                height_1st = str(WIDTH * float(height_1st))
                width_3rd = str(HEIGHT * float(width_3rd))
                height_3rd = str(WIDTH * float(height_3rd))

                point = [[width_1st, height_1st], [width_3rd, height_3rd]]
                item_dict = {'label':state, 'line_color':None,'fill_color':None, 'points':point,"shape_type": "rectangle","flags": {}}
                new_data['shapes'].append(item_dict)
            new_data['imagePath'] = pic_save_path
            new_data["imageData"] = None
            new_data["imageHeight"] = HEIGHT
            new_data["imageWidth"] = WIDTH
            with open(json_path, 'w') as f:
                json.dump(new_data, f, indent=4, ensure_ascii=False)
            return HttpResponse("finish")
        except Exception as e:
            return HttpResponse(e)

def shareget(request):
    allusers = User.objects.all()
    usernames = ";".join([user.user_name for user in allusers])
    return HttpResponse(usernames)

def share(request):
    user_name = request.POST.get('user_name')
    rtsp_ip = request.POST.get('rtsp_ip')
    user = User.objects.filter(user_name=user_name)
    if user:
        temp_data={"cam_ip_add" : str(user[0].cam_id.cam_ip),
                    "rtsp_ip" : str(user[0].cam_id.rtsp_ip)
                }
        client.sadd("share", json.dumps(temp_data))
        print('分享开始')
        return HttpResponse("邀请" + user_name + "信息已发送")
    else:
        print('分享失败')
        return HttpResponse()
    # password = request.POST.get('pwd')

# 网页用户登录
def logins(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        assert password or username
    #     # 通过姓名查找用户信息
        user = User.objects.filter(user_name=username, pwd=password)
        if user:
            if user.authority == "1":
                request.session['is_login']='1'
                return redirect('users/')
            else: 
                messages.error(request,'该用户无管理员权限，如需权限请联系管理员')
                return render(request,'logins.html')
        else:
            messages.error(request,'账号密码错误，如需修改请联系管理员')
            return render(request,'logins.html')
    return render(request,'logins.html')


@check_login
def queryUsers(request):
    us = User.objects.all()
    camls = Cam.objects.all()
    context = {
        'ls' : us,
        'camls' : camls,
    }
    return render(request, "users.html", context)

@check_login
def openAdd(request):
    return render(request, "userAdd.html")

@check_login
def saveUser(request):
    user = User()
    try:
        user.user_name = request.GET.get('user_name')
        user.email = request.GET.get('email')
        user.password = request.GET.get('pwd')
        user.authority = request.GET.get('authority')
        # cam_id = request.GET.get('cam_id')
        user.cam_id = Cam.objects.get(id = request.GET.get('cam_id'))
    except:
        error_message = "输入不合法或为空,请检查输入内容！"
        context = {
            "error_message":error_message,
            "m":user,
        }
        return render(request,'userAdd.html',context)

    
    if(User.objects.filter(user_name = user.user_name)):
        error_message = "用户名重复"
        context = {
            "error_message":error_message,
            "m":user,
        }
        return render(request, "userAdd.html", context)
    else:
        User.objects.create(user_name = user.username, email = user.email, pwd = user.password, authority = user.authority, cam_id = user.cam_id )
        return redirect("/queryUsers")

@check_login
def openEdit(request):
    id = request.GET.get('id')
    # 到数据库查询用户信息
    m = User.objects.filter(id=id).first()
    # 将数据发给页面
    context = {"m": m}
    return render(request, "userEdit.html", context)

@check_login
def updateUser(request):
    id = request.GET.get('id')
    currentuser = get_object_or_404(User,id=id)

    m = User()
    m.pk = id

    # username = request.GET.get('user_name')
    # password = request.GET.get('password')
    # User.objects.filter(id=id).update(username=username, password=password)
    # return redirect("/queryUsers")
    try:   
        m.user_name = request.GET.get('user_name')
        m.email = request.GET.get('email')
        m.pwd = request.GET.get('pwd')
        m.authority = request.GET.get('authority')
        m.cam_id = Cam.objects.get(id = request.GET.get('cam_id'))      
    except:
        error_message = "输入不合法或为空,请检查输入内容！"
        context = {
            "error_message":error_message,
            "m":m,
        }
        return render(request, "userEdit.html", context)
    # 若更改了用户名则查询数据库,判断是否重名,否则跳过检查
    if ((currentuser.user_name != m.user_name) and (User.objects.filter(user_name=m.user_name).first())):
        error_message = "用户名重复"
        context = {
            "error_message":error_message,
            "m":m,
        }
        return render(request, "userEdit.html", context)
    else:
        User.objects.filter(id=id).update(user_name=m.user_name,email = m.email, pwd=m.pwd, authority = m.authority, cam_id = m.cam_id)
        return redirect("/queryUsers")
 

@check_login    #删除数据
def deleteUser(request):
    id = request.GET.get('id')
    print(id)
    User.objects.filter(id=id).delete()
    return redirect("/queryUsers")


#rtsp_ip 不可重复
def camAdd(request):
    
    us = User.objects.all()
    camls = Cam.objects.all()

    cam = Cam()
    cam.ip = request.GET.get('ip')
    cam.rtsp_ip = request.GET.get('rtsp_ip')

    if Cam.objects.filter(rtsp_ip = cam.rtsp_ip):
        error_message = "rtsp_ip重复"
        context = {
            "messages":error_message,
            'ls' : us,
            'camls' : camls,
        }
        return render(request, "users.html", context)
    else:
        Cam.objects.create(cam_ip = cam.ip, rtsp_ip = cam.rtsp_ip)
        return redirect("/queryUsers")

def deleteCam(request):
    id = request.GET.get('id')
    Cam.objects.filter(id=id).delete()
    return redirect("/queryUsers")

def openCamEdit(request):
    id = request.GET.get('id')
    cam = Cam.objects.filter(id=id).first()
    context = {"cam": cam}
    return render(request, "camEdit.html", context)

def updateCam(request):
    id = request.GET.get('id')
    ip = request.GET.get('ip')
    rtsp_ip = request.GET.get('rtsp_ip')
    print(id,ip,rtsp_ip)
    Cam.objects.filter(id=id).update(cam_ip = ip, rtsp_ip = rtsp_ip)
    return redirect("/queryUsers")


# 测试用

#登录验证
def login_venrify(request):
    # if request.method == 'GET':
        # userform = UserForm(request.POST)
        # if userform.is_valid():
    print(11111111111111111)
    username = request.POST.get('username')
    password = request.POST.get('password')
        # 通过姓名查找用户信息
    result=2
    user = User.objects.filter(user_name = username ,pwd = password).first()
    print(user)
    if user:
        request.session['username'] = username
        print(request.session['username'])
        result = 0
    else:
        result = 1
    #传js中选择跳转
    return JsonResponse({"result": result})

#首页

# @login_required
def index(request):
    username = request.session.get('username')
    return render(request,"index.html",{"username":username})

#表的展示
def open_users(request):
    return render(request, "userinfo/userinfoInfo.html")

#添加用户页面
def open_add(request):
    return render(request,"userinfo/userinfoAdd.html")

#添加摄像头页面
def open_add_cam(request):
    return render(request,"caminfo/caminfoAdd.html")

#添加USERs表功能
def save_user(request):
    user_name = request.POST.get('user_name')
    password = request.POST.get('pwd')
    authority = request.POST.get('authority')
    email = request.POST.get('email')
    cam_id =Cam.objects.get(id = request.POST.get('cam_id'))
    result = -1
    if User.objects.filter(user_name=user_name).first():
        result = 1
    else:
        User.objects.create(user_name=user_name, pwd=password,authority=authority,cam_id=cam_id,email=email)
        result = 0
    return JsonResponse({"result": result})

#添加Cams表功能
def save_cam(request):
    IP = request.POST.get('cam_ip')
    rtsp_ip = request.POST.get('rtsp_ip')
    result = -1
    if Cam.objects.filter(rtsp_ip=rtsp_ip).first():
        result = 1
    else:
        Cam.objects.create(cam_ip=IP, rtsp_ip=rtsp_ip)
        result = 0
    return JsonResponse({"result": result})


#删除表功能
def delete_user(request):
    id = request.POST.get('id')
    obj = User.objects.filter(id=id).delete()
    result = -1
    if obj:
        result = -1
    print(id,obj)
    return JsonResponse({"result": result})

def delete_cam(request):
    id = request.POST.get('id')
    obj = Cam.objects.filter(id=id).delete()
    result = -1
    if obj:
        result = -1
    print(id,obj)
    return JsonResponse({"result": result})

#查询用户信息和跳转
def open_edit_Users(request):
    id = request.GET.get('id')
    # 到数据库查询用户信息
    m = User.objects.filter(id=id).first()
    # 将数据发给页面
    context = {"m": m}
    print(id)
    return render(request, "userinfo/userinfoEdit.html", context)

#查询摄像头那一行信息
def open_edit_Cam(request):
    id = request.GET.get('id')
    # 到数据库查询用户信息
    m = Cam.objects.filter(id=id).first()
    # 将数据发给页面
    context = {"m": m}
    print(id)
    return render(request, "caminfo/caminfoEdit.html", context)
    
#编辑用户功能
def update_user(request):
    id=request.POST.get('id')
    
    user_name = request.POST.get('user_name')
    password = request.POST.get('pwd')
    authority = request.POST.get('authority')
    email = request.POST.get('email')
    cam_id =Cam.objects.get(id = request.POST.get('cam_id'))  
    print(id,user_name,password,authority,email)

    result = -1
    if User.objects.filter(user_name=user_name).first():
        result = -1
    else:
        User.objects.filter(id=id).update(user_name=user_name, pwd=password,authority=authority,email=email,cam_id=cam_id)
    result = 0
    return JsonResponse({"result": result})

#编辑摄像头ip功能
def update_cam(request):
    id=request.POST.get('id')
    IP = request.POST.get('cam_ip')
    rtsp_ip = request.POST.get('rtsp_ip')

    result = -1
    if Cam.objects.filter(cam_ip=IP).first() or Cam.objects.filter(rtsp_ip=rtsp_ip).first():
        result = -1
    else:
        Cam.objects.filter(id=id).update(cam_ip=IP,rtsp_ip=rtsp_ip)
        result = 0
    return JsonResponse({"result": result})

#分页 和 显示用户表信息
def query_Users(request):
    limit = request.GET.get("limit")
    page = request.GET.get("page")
    id =request.GET.get("id")
    print(id)
    us=[]
    if id=='':
        us = User.objects.all()
    else:
        us = User.objects.filter(id=id)
    paginator = Paginator(us, limit)
    p_list = paginator.page(page).object_list
    count = paginator.count
    json_list = []
    for v in p_list:
        json_dict = model_to_dict(v)
        json_list.append(json_dict)
    data_j = json.dumps(json_list)
    data_json = json.loads(data_j)
    # 将数据发给页面
    context = {"code": 0, "data": data_json, "count": count, "msg": ""}
    return JsonResponse(context)


#分页 和 显示ip表信息
def query_Cams(request):
    limit = request.GET.get("limit")
    page = request.GET.get("page")
    us = Cam.objects.all()
    paginator = Paginator(us, limit)
    p_list = paginator.page(page).object_list
    count = paginator.count
    json_list = []
    for v in p_list:
        json_dict = model_to_dict(v)
        json_list.append(json_dict)
    data_j = json.dumps(json_list)
    data_json = json.loads(data_j)
    # 将数据发给页面
    context = {"code": 0, "data": data_json, "count": count, "msg": "数据"}
    return JsonResponse(context)


def out_login(request):
    request.session['username'] = None
    return render(request, "logins.html")

def control_main(request):
    return render(request,"control.html")

def control(request):
    id=request.POST.get('id')
    val=os.system('pwd')
    if id=="启用":
        # val = os.system('python3 ./redis/camera-1.py')
        # print(val)
        result = 1
    else:
        result = 0
        print()
        print(client.dbsize())
        a= client.scan ( 0 , "share*" , 100000 )
        return_pos , datalist = a
        print ( time . strftime ( "%Y-%m-%d %H:%M:%S" , time . localtime ( time . time ( ) ) ) , return_pos )
        print(len ( datalist ))
        if len ( datalist )!=0:
            print ( time . strftime ( "%Y-%m-%d %H:%M:%S" , time . localtime ( time . time ( ) ) ) , "delete" , len ( datalist ) )
            client . delete ( * datalist )
        print(a)
    return JsonResponse({"result": result})

if __name__ == '__main__':
    print(dev_info_list)
