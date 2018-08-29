#coding:utf-8

from django.db import models

class Histories(models.Model):
    '''
    Histories 类描述用户访问历史之间的关联性
    firstId 和  secondId 之间是平级的, 没有主次之分
    '''
    id = models.BigAutoField(primary_key=True)
    firstId = models.BigIntegerField(db_index=True)
    secondId = models.BigIntegerField(db_index=True)
    count = models.BigIntegerField()
    def __str__(self):
        return 'firstId:' + self.firstId.__str__() + '; secondId:' + self.secondId.__str__() + '; count:' + self.count.__str__()
    
    class Meta:
        managed = False
        db_table = 'histories'
