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

class Datastore(models.Model):
    id = models.BigIntegerField(primary_key=True)
    serial_no = models.CharField(max_length=50)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    contents = models.TextField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    domain = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=50, blank=True, null=True)
    topic = models.CharField(max_length=250, blank=True, null=True)
    source = models.CharField(max_length=250, blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    province = models.TextField(blank=True, null=True)
    data_time = models.TextField(blank=True, null=True)
    file_name = models.CharField(max_length=500, blank=True, null=True)
    file_size = models.CharField(max_length=250, blank=True, null=True)
    file_type = models.CharField(max_length=20, blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)
    publish_time = models.DateTimeField(blank=True, null=True)
    create_user = models.CharField(max_length=50, blank=True, null=True)
    update_user = models.CharField(max_length=50, blank=True, null=True)
    publish_user = models.CharField(max_length=50, blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ispublic = models.IntegerField(db_column='isPublic', blank=True, null=True)  # Field name made lowercase.
    readhot = models.IntegerField()
    downloads = models.IntegerField()
    praise = models.IntegerField()
    subscribesum = models.IntegerField()
    geotype = models.CharField(max_length=20, blank=True, null=True)
    ref_id = models.CharField(max_length=50, blank=True, null=True)
    def __str__(self):
        return self.title
    
    class Meta:
        managed = False
        db_table = 'datastore'