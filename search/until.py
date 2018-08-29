#coding:utf-8

from django.conf import settings
from django.utils.dateparse import parse_datetime
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections
from search.suggestion import getSuggestions, countDownloads
import requests, json 


# Render the search-result detail page
def getItem(itemId):
    # handle id here
    # TODO 
    body = {
        "query": {
            "term": {
                "id": itemId
                }
            }
        }
    
    until = Until()
    response = until.doSearch(body)
    
    if response and len(response.hits) > 0:
        hit = response.hits[0]
        
        ref_id_title = ''
        if hit.ref_id:
            # get the title if ref_id exists
            ref_id_title = until.getRefIdTitle(hit.ref_id)
        
        # 获取推荐的 itemId 集合
        suggestIds = getSuggestions(itemId, 5, 3)
        recommends = until.getRecommendedIdTitles(suggestIds)
        
        params = {
            'id': str(hit.id),
            'meta_id': hit.meta.id,
            'keywords': hit.keywords,
            'title': hit.title,
            'contents': hit.contents,
            'price': hit.price,
            'level': hit.level,
            'source': hit.source,
            'data_time': hit.data_time,
            'publish_time': until.dateFormat(hit.publish_time),
            'readhot': hit.readhot + 1,
            'downloads': hit.downloads,
            'ref_id': str(hit.ref_id),
            'ref_id_title': ref_id_title,
            'recommends': recommends
            }
        
        until.updateFieldCount(hit.meta.id, 'readhot')
    else:
        return None
    
    return params

# the search API, handle the search request
# and get the filter tree 
def getTree(keyword, pageNo, filterList, orderby_val):
    until = Until()
    orderby = ["readhot", "publish_time"]
    
    pageNo = int(pageNo)
    # display no more than 10000 results
    if pageNo > settings.MAX_RESULTS_PAGES_DISPLAYED:
        pageNo = settings.MAX_RESULTS_PAGES_DISPLAYED
    
    start_from = (int(pageNo) - 1) * 10;
    
    query = {}
    if len(keyword.strip()) > 0:
        # query for keywords
        query = {
            "multi_match": {
                "query": keyword,
                "fields": [
                    "title",
                    "description",
                    "contents",
                    "keywords",
                    "industry",
                    "topic",
                    "source",
                    "data_time"
                    ],
                }
            }
    else:
        # query for all the list 
        query = {
            "match_all": {}
            }
    
    boolBody = until.getESQueryFromChecked(filterList, query)
    
    body = {
        "query": boolBody,
        "from": start_from,
        "size": 10,
        "sort": [
            {orderby[orderby_val]: {
                "order": "desc"
                }
            },
            "_score",
            "id"
        ],
        "aggs": {
            "by_domain_industry": {
                "terms": {
                    "field": "domain.keyword",
                    "size": 999,
                    "min_doc_count":0,
                    "order": {
                        "_key": "asc"
                    }
                },
                "aggs": {
                    "industry_stats": {
                        "terms": {
                            "field": "industry.keyword",
                            "size": 999,
                            "order": {
                                "_key": "asc"
                                }
                            }
                        }
                    }
                }
            }
        }
    
    response = until.doSearch(body)
    if not response:
        return None
    
    # # by indicating extra(size=0), we can make it more effecient 
    # s = Search(using=client, index="search_engine_data").query("match_all").extra(size=10)
    # # 聚合查询，用domain字段的值来查询每个相同的title对应的count数
    # a = A('terms', field='domain.keyword', size=99999999)
    # b = A('terms', field='domain.keyword', size=99999999)
    # s.aggs.bucket('by_domain', a)
    # response = s.execute()
    
    hit_list = []
    
    # for bucket in response.aggs.bucket:
    for hit in response.hits:
        description = hit.description
        title = hit.title
        data_time = hit.data_time
        source = hit.source
        
        if len(keyword.strip()) > 0:
            if hasattr(hit.meta, "highlight"):
                if hasattr(hit.meta.highlight, "title"):
                    title = hit.meta.highlight.title[0]
                if hasattr(hit.meta.highlight, "description"):
                    description = hit.meta.highlight.description[0]
                if hasattr(hit.meta.highlight, "data_time"):
                    data_time = hit.meta.highlight.data_time[0]
                if hasattr(hit.meta.highlight, "source"):
                    source = hit.meta.highlight.source[0]
        
        hit_list.append({
            'id': str(hit.id),
            'title': title,
            'description': description,
            'source': source,
            'data_time': data_time,
            'publish_time': until.dateFormat(hit.publish_time),
            'readhot': hit.readhot,
            'downloads': hit.downloads
            })
    
    group_list = []
    parent_index = 0
    # for bucket in response.aggs.bucket:
    for bucket in response.aggregations.by_domain_industry.buckets:
        parent_index = parent_index + 1
        children = []
        child_index = 0
        for child in bucket.industry_stats.buckets:
            child_index = child_index + 1
            children.append({
                'key': ''.join([str(parent_index), "-", str(bucket.key), "-", str(child_index), "-", child.key]), 
                'checked': False,
                'title': child.key,
                'count': child.doc_count
            })
        # parents nodes
        group_list.append({
            'key': ''.join([str(parent_index), "-", bucket.key]), 
            'count': bucket.doc_count,
            'title': bucket.key,
            'expand': False,
            'hasChildren':len(children) > 0,
            'children': children
            })
    
    list_total = response.hits.total
    # if list_total > settings.MAX_RESULTS_PAGES_DISPLAYED:
    #    list_total = settings.MAX_RESULTS_PAGES_DISPLAYED
    
    responseData = {
        'code': 200,
        'message': 'OK',
        'query': filterList,
        'body': body,
        'took': response.took,
        'data': {
            'filter': group_list,
            'list': {
                'data': hit_list,
                'total': list_total
                }
            }
        }
    
    return responseData

def updateDownload(meta_id, itemId):
    if meta_id:
        try:
            Until().updateFieldCount(meta_id, 'downloads')
            countDownloads(itemId)
            responseData = {
                'code': 200,
                'message': 'OK',
                }
        except Exception as e:
            responseData = {
                'code': 200,
                'message': e.__str__(),
                }
        finally:
            pass
    else:
        responseData = {
            'code': 200,
            'message': 'NO MATCHED ID FOUND',
            }
    
    return responseData
    

class Until:
    
    def doSearch(self, body):
        try:
            client = connections.create_connection(hosts=[settings.ES_URL])
            s = Search(using=client, index=settings.ES_INDEX_NAME, doc_type=settings.ES_INDEX_TYPE)
            s = Search.from_dict(body)
            s = s.index(settings.ES_INDEX_NAME)
            s = s.doc_type(settings.ES_INDEX_TYPE)
            
            # hightlight the following fields in the search result
            s = s.highlight('title')
            s = s.highlight('description')
            s = s.highlight('data_time')
            s = s.highlight('source')
            
            body = s.to_dict()
            response = s.execute()
        except Exception:
            return None
        
        return response
    
    def dateFormat(self, date_str):
        try:
            result = parse_datetime(date_str).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            result = date_str
        finally:
            return result
    
    # field - readhot/downloads
    def updateFieldCount(self, es_id, field):
        # url = 'http://127.0.0.1:9200/datastore/doc/8tiNEmUBw7RIvfsV9-Cj/_update'
        url = '/'.join([settings.ES_URL, settings.ES_INDEX_NAME, settings.ES_INDEX_TYPE, es_id, '_update'])
        data = {
            "script": {
                "inline": "ctx._source." + field +" += 1"
                }
            }
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(url=url, headers=headers, data=json.dumps(data)) 
        except Exception:
            pass
        finally:
            return response
    
    # get the title according to the id
    def getRefIdTitle(self, itemId):
        body = {
            "query": {
                "term": {
                    "id": itemId
                    }
                }
            }
        response = self.doSearch(body)
        
        if response and len(response.hits) > 0:
            return response.hits[0].title
        else:
            return ''
    
    # get what other users viewed 
    def getRecommendedIdTitles(self, ids):
        if ids and len(ids) > 0:
            body = {
                "query": {
                    "terms": {
                        "id": ids
                        }
                    }
                }
            response = self.doSearch(body)
            
            if response and len(response.hits) > 0:
                hit_list = []
                for hit in response.hits:
                    hit_list.append({
                        'id': str(hit.id),
                        'title': hit.title
                    })
                return hit_list
        # no match
        return []
    
    def makeUpFilterList(self, filterList):
        # "1-传播,1-传播-1-媒体,1-传播-2-媒体测试,2-商业-1-贸易,3-民生,3-民生-1-社保,3-民生-2-社保测试"
        madeUpList = []
        fList = str.split(',')
        for item in fList:
            arr = item.split('-')
            
            if len(arr) == 2:
                madeUpList.append(item)
            elif len(arr) == 4:
                madeUpList.append(item)
        
        return filterList
    
    def getESQueryFromChecked(self, filterList, mustQuery):
        if len(filterList) == 0:
            return {
                "bool": {
                    "must": mustQuery
                    }
                }
        
        # "1-传播,1-传播-1-媒体,1-传播-2-媒体测试,2-商业,2-商业-1-贸易,3-民生,3-民生-1-社保,3-民生-2-社保测试"
        filterStr = self.formatFilterList(filterList)
        fList = filterStr.split(',')
        should = []
        must = []
        industry_should = []
        for item in fList:
            arr = item.split('-')
            
            if len(arr) == 2:
                if len(must) > 0:
                    should.append({
                        "bool": {
                            "must": must,
                            "should": industry_should,
                            "minimum_should_match": 1
                            }
                        })
                must = []
                industry_should = []
                must.append({
                    "term": {
                        "domain" : arr[1]
                        }
                    })
            elif len(arr) == 4:
                industry_should.append({
                    "term": {
                        "industry" : arr[3]
                        }
                    })
        should.append({
            "bool": {
                "must": must,
                "should": industry_should ,
                "minimum_should_match": 1
                }
            })
        
        return {
            "bool": {
                "must": mustQuery,
                "should": should,
                "minimum_should_match": 1
                }
            }
    
    def formatFilterList(self, filterList):
        # "1-传播,1-传播-1-媒体,1-传播-2-媒体测试,2-商业-1-贸易,3-民生,3-民生-1-社保,3-民生-2-社保测试"
        fList = filterList.split(',')
        
        result = []
        
        currentDomain = ''
        index = 0
        for item in fList:
            # print(item)
            arr = item.split('-')
            if len(arr) == 4:
                if index == 0:
                    # if the first item is industry
                    currentDomain = '-'.join([arr[0], arr[1]])
                    result.append(currentDomain)
                elif currentDomain != arr[1]:
                    currentDomain = '-'.join([arr[0], arr[1]])
                    result.append(currentDomain)
            
            result.append(item)
            currentDomain = arr[1]
            index = index + 1
        return ','.join(result)
    



