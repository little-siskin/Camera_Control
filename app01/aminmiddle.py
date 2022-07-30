from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from app01.models import User, Cam

class Aminmiddle(MiddlewareMixin):
    def process_request(self, request):
        print("访问路径为", request.path)
        if request.path == '/' or request.path == '/tagging/' or request.path == 'out_login/' or request.path == '/shareget/'or request.path == '/share/' or request.path == '/detection/' or request.path == '/stoppushing/':
            return None
        else:
            v = request.POST.get('username')
            z = request.session.get('username') 
            # password = request.POST.get('password')
            # user = User.objects.filter(user_name = v ,pwd = password).first()
            # print(user)
            # print(v,password)
            if v or z:
                return None
            else:
                print('url直接访问')
                return redirect('/')
