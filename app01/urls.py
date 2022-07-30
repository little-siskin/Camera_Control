from django.conf.urls import url,include
from django.contrib import admin
from app01 import views

from django.urls import path
admin.autodiscover()

app_name = 'app01'

urlpatterns = [

    # 新增代码 Start
    path('', views.logins, name = "logins"),
    #url('logout/', views.logouts, name = "logout"),
    path('login_venrify/',views.login_venrify),
    path('camAdd/', views.camAdd),
    path('index/',views.index),
    path('deleteCam/', views.deleteCam),
    path('openCamEdit/', views.openCamEdit),
    path('updateCam/', views.updateCam, name = "updateCam"),
    path('out_login',views.out_login),
    path('control_main/',views.control_main),
    path('control_main/control/',views.control),

    
    #数据库操作
    url('queryUsers1/',views.query_Users),
    url('queryUsers2/',views.query_Cams),
    path('openUsers/', views.open_users),
    path('openUsers/openUserAdd', views.open_add),
    path('openUsers/openCamAdd', views.open_add_cam),
    path('openUsers/saveUser', views.save_user),
    path('openUsers/saveCam', views.save_cam),
    path('openUsers/update_user',views.update_user),
    path('openUsers/update_cam',views.update_cam),
    path('openUsers/deleteUser', views.delete_user),
    path('openUsers/deleteCam', views.delete_cam),
    path('openUsers/openEdit_Users', views.open_edit_Users),
    path('openUsers/openEdit_Cams', views.open_edit_Cam),
    # End

    url('users/',views.queryUsers, name= "userIndex"),
    url('logins/',views.logins),
    url('regist/',views.regist, name="regist"),

    url('queryUsers/', views.queryUsers),
    url('openUserAdd/', views.openAdd),
    url('saveUser/', views.saveUser),
    url('openEdit/', views.openEdit),
    url('updateUser/', views.updateUser),
    url('deleteUser/', views.deleteUser),

    # 手机
    url('login/',views.login),
    url('stoppushing/',views.stoppushing),
    url('shareget/', views.shareget),
    url('share/',views.share),
    url('detection/',views.detection),
    url('tagging/', views.tagging),
]
