#coding:utf-8

"""search_engine URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# 引入search应用下的view模块
import search.views as sv

from django.conf.urls import handler404

urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    # url(r'^index/', include("search.urls", namespace="search")),	# 添加index，作为访问目录
    path('admin/', admin.site.urls),
    path('', include("search.urls")),	# 添加index，作为访问目录
]

# https://docs.djangoproject.com/en/2.0/topics/http/views/#customizing-error-views
handler404 = 'search.views.handler404' 
