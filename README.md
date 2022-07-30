# 修改内容

    因为用 redis 会有信息残留、摄像头不能退出导致不能重新获取和不能多用户操作的问题，
    这次修改将 redis 换成了多线程。

    1. camera-1.py -> app01/task_consumer.py
       不需要启动 camer-1.py

    2. app01/views.py

       函数:  login,  detection,  tagging  这三个主要函数做对应修改


# BUG

    1. 重定向 (未解决)
    
        发送 stoppushing, detection, tagging 指令时会重定向到 logins(根据规则 Camera_Control_multiprocess/urls.py 中的 url('', views.logins))
        测试其他功能时可以把 logins 中的注释取消来测试对应函数
        

        

# 修改内容 2022.05.20

    1. android TextureViewListener.java 96行 options.add("--rtsp-tcp") 预览时延

    2. detection: 手机端发送检测命令，服务器端检测当前摄像头下的图片，并将检测结果返回，手机端收到检测结果，并将检测结果显示出来

    3. tagging: 手机端标注当前图片，服务器端收到标注信息并将其保存为json格式，然后服务器保存对应的图片和json。
