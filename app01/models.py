from django.db import models

from django.contrib import admin
# Create your models here.

class User(models.Model):
    user_name = models.CharField(max_length = 30, null = False)
    email = models.EmailField()
    pwd = models.CharField(max_length = 30, null = False)
    authority = models.CharField(max_length = 2, choices=(('0', 'User'),('1', 'Admin')), default = '0')
    cam_id = models.ForeignKey('Cam', on_delete = models.CASCADE, verbose_name = '相机id')

class Cam(models.Model):
    cam_ip = models.CharField(max_length = 250, null = False)
    rtsp_ip = models.CharField(max_length = 250, null = False)

class UserAdmin(admin.ModelAdmin):
    list_display = ('user_name','pwd','email')
 
admin.site.register(User,UserAdmin)
admin.site.register(Cam)
