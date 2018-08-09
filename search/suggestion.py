#coding:utf-8

from django.http.request import HttpRequest
from django.db import connection
from django.db.models import Q
from .models import Histories
import random

def checkLogined():
    '''
    checkLogined 方法判断当前用户是否处于登录状态
    '''
    return True

def saveHistory(HttpRequest, selectedId):
    '''
    saveHistory 方法用于处理 session , 并将关联结果存入数据库
    @HttpRequest: 从 view.py 中传递的 request
    @return: 对 session 进行处理后的 request
    '''
    his = History(HttpRequest)
    return his.addHistory(selectedId)

def getSuggestions(selectedId, maxRecords, maxViews):
    '''
    getSuggestions 方法依据当前详情页面 id 的值, 返回与其相关联的其它 id 的集合
    @selectedId: 当前详情页面的 id
    @maxRecords: 从数据库中取得的最大记录数
    @maxViews: 需要返回的最大记录数
    @return: 与当前详情页面的 id 相关联的其它 id 的集合
    '''
    sug = Suggest(selectedId)
    return sug.getSuggestIds(maxRecords, maxViews)

def countDownloads(selectedId):
    '''
    countDownloads 方法依据当前详情页面 id 的值操作数据库, 更新 datastore 表中的 downloads 字段
    @selectedId: 当前详情页面的 id
    '''
    MySQLConnect().updateDownloads(selectedId)


class History:
    '''
    History 类用于创建存储用户访问历史的容器, 以及对容器内的历史数据进行遍历, 将关联数据存入数据库
    该类应该在 view.py 中被引用
    '''
    
    def __init__(self, HttpRequest):
        '''
        构造一个新的对象实例
        @HttpRequest: 从 view.py 中传递的 request
        '''
        self.request = HttpRequest
    
    def createSession(self):
        '''
        createSession 方法判断当前用户会话是否已经创建存储容器, 如果未创建将初始化存储容器
        @return: 对 session 进行处理后的 request
        '''
        # 如果不是登录用户将不保存历史访问记录, 也不将历史访问记录加入推荐统计列表
        if checkLogined():
            if not self.request.session.get('ids'):
                self.request.session['ids'] = []
                # print('create ids')
        return self.request
    
    def addHistory(self, selectedId):
        '''
        addHistory 方法将用户当前访问的页面的 id 与 session 中已保存的 id 进行遍历, 将关联结果存入数据库
        @selectedId: 当前页面的 id
        @return: 对 session 进行处理后的 request
        '''
        MySQLConnect().updateReadhot(selectedId)
        # 如果用户是直接访问详情页面而不是经由列表页面访问详情页面, 应该为其创建存储容器
        self.createSession()
        # 如果不是登录用户将不保存历史访问记录, 也不将历史访问记录加入推荐统计列表
        if checkLogined():
            idList = self.request.session['ids']
            # 如果当前页面 id 不存在于存储容器时, 当前页面为本次会话新访问到的页面
            if selectedId not in idList:
                # print(selectedId.__str__() + ' is not in idList')
                # 遍历存储容器中已保存的所有 id 
                for savedId in idList:
                    try:
                        # 交叉判断 savedId 和 id 分别为 firstId 和 secondId 时的情况, 将任何满足条件的数据库记录取出
                        savedHistory = Histories.objects.get(Q(firstId=savedId, secondId=selectedId)|Q(firstId=selectedId, secondId=savedId))
                    except Exception:
                        # 如果未能查找到相关记录, 将视为这是一个新的关联组合, 创建并将其存入数据库
                        history = Histories(firstId=savedId, secondId=selectedId, count=1)
                        history.save()
                    else:
                        # 将获取到的数据库记录统计加1, 更新这条记录
                        savedHistory.count += 1
                        savedHistory.save()
                # 将当前页面 id 添加进存储容器中
                self.request.session['ids'] += [selectedId]
        return self.request

class Suggest:
    '''
    Suggest 类用于查找与当前详情页面的 id 相关联的其它详情页面的 id , 并按统计值 count 降序排列
    '''
    def __init__(self, selectedId):
        '''
        构造一个新的对象实例
        @selectedId: 当前详情页面的 id
        '''
        self.selectedId = selectedId
    
    def getSuggestIds(self, maxRecords, maxViews):
        '''
        getSuggestIds 方法用于返回相关联的 id 的集合
        @maxRecords: 从数据库中取得的最大记录数
        @maxViews: 需要返回的最大记录数
        @return: 与当前详情页面的 id 相关联的其它 id 的集合
        '''
        suggestIds = []
        try:
            # 从数据库中取得 firstId 和 secondId 分别为当前 id 的值的记录, 按统计降序排列
            histories = Histories.objects.filter(Q(firstId=self.selectedId)|Q(secondId=self.selectedId)).order_by('-count')[:maxRecords]
        except Exception:
            print('db error')
        else:
            # 如果取得的记录数大于需要显示的记录数, 则随机获取需要显示的记录
            if histories.count() > maxViews:
                subHistories = random.sample(list(histories), maxViews)
                for history in subHistories:
                    # print(history)
                    suggestIds += [self.getReturnId(history)]
            else:
                for history in histories:
                    # print(history)
                    suggestIds += [self.getReturnId(history)]
        return suggestIds
    
    def getReturnId(self, history):
        '''
        getReturnId 方法用于比对当前详情页面的 id 的值， 将非当前详情页面的 id 的值进行返回
        @return: 与当前详情页面的 id 相关联的其它 id
        '''
        fId = history.firstId
        sId = history.secondId
        if fId == self.selectedId:
            return sId
        else:
            return fId
        
class MySQLConnect:
    '''
    MySQLConnect 类用于创建与 mysql 数据库的连接并执行相关数据库操作
    '''

    def __init__(self):
        '''
        构造一个新的对象实例
        '''
    
    def updateReadhot(self, selectedId):
        '''
        更新查看次数字段的值
        @selectedId: 当前详情页面的 id
        '''
        try:
            self.cursor = connection.cursor()
            self.cursor.execute("""UPDATE datastore SET readhot = readhot + 1 WHERE id = %s""", [selectedId])
            self.cursor.close()
        except Exception:
            print('failed to update readhot')
        
    def updateDownloads(self, selectedId):
        '''
        更新下载次数字段的值
        @selectedId: 当前详情页面的 id
        '''
        try:
            self.cursor = connection.cursor()
            self.cursor.execute("""UPDATE datastore SET downloads = downloads + 1 WHERE id = %s""", [selectedId])
            self.cursor.close()
        except Exception:
            print('failed to update downloads')
        