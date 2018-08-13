"""mysite URL Configuration

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
from django.urls import path

# 引入search应用下的view模块
from . import views as sv

# # https://docs.djangoproject.com/en/2.0/topics/http/views/#customizing-error-views
handler404 = 'views.handler404'

urlpatterns = [
    path('', sv.search, name='base'),	         # 
    path('item/<int:id>/', sv.item, name='id'),  # 添加item/docid，作为详情访问目录
    path('tree', sv.getree),	                 # 添加tree，作为filter数据访问目录
    path('update', sv.update),                   # 添加update
]

