from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, A, FacetedSearch, TermsFacet, DateHistogramFacet
from elasticsearch_dsl.connections import connections

from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render
from django.conf import settings
from django.utils.dateparse import parse_datetime

from search.suggestion import History, Suggest, saveHistory, getSuggestions, countDownloads
from search.models import Datastore

import time, datetime, requests, json 


# Render the list page
def search(request):
  return render(request, 'search/list.html', {})

# Update downloads count
def update(request):
  meta_id = request.POST.get('meta_id', '')
  id = request.POST.get('id', '')

  responseData = {
    'code': 200,
    'message': 'OK',
  }

  if meta_id:
    try:
      updateFieldCount(meta_id, 'downloads')

      countDownloads(id)

    except Exception as e:
      print(e)
    finally:
      pass
  else:
    responseData = {
      'code': 200,
      'message': 'NO MATCHED ID FOUND',
    }

  return JsonResponse(responseData)


# Render the search-result detail page
def item(request, id):
  # handle id here
  # TODO 
  body = {
    "query":{
      "term":{
            "id": id
         }
    }
  }

  # call method
  request = saveHistory(request, id)

  response = doSearch(body)

  
  # 获取推荐 id 测试
  suggestIds = getSuggestions(id, 3, 3)
  recommends = getRecommendedIdTitles(suggestIds)

  params = {}
  if len(response.hits) > 0:
    hit = response.hits[0]

    ref_id_title = ''
    if hit.ref_id:
      # get the title if ref_id exists
      ref_id_title = getRefIdTitle(hit.ref_id)

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
      'publish_time': dateFormat(hit.publish_time), 
      'readhot': hit.readhot,
      'downloads': hit.downloads,
      'ref_id': str(hit.ref_id), 
      'ref_id_title': ref_id_title,
      'recommends': recommends
    }

    updateFieldCount(hit.meta.id, 'readhot')

  else:
    raise Http404("Item not found.")

  return render(request, 'search/detail.html', params)

def dateFormat(date_str):
  try:
    result = parse_datetime(date_str).strftime("%Y-%m-%d %H:%M:%S")
  except Exception as e:
    result = date_str
  finally:
    return result

# field - readhot/downloads
def updateFieldCount(es_id, field):
  # url = 'http://127.0.0.1:9200/datastore/doc/8tiNEmUBw7RIvfsV9-Cj/_update'
  url = '/'.join([settings.ES_URL, settings.ES_INDEX_NAME, settings.ES_INDEX_TYPE, es_id, '_update'])
  data = {"script":{"inline":"ctx._source." + field +" += 1"}}
  headers = {'Content-Type': 'application/json'}
  try:
    response = requests.post(url=url, headers=headers, data=json.dumps(data)) 
  except Exception as e:
    pass
  finally:
    return response  


# get the title according to the id
def getRefIdTitle(id):
  body = {
    "query":{
      "term":{
            "id": id
         }
    }
  }
  response = doSearch(body)

  if len(response.hits) > 0:
    return response.hits[0].title
  else:
    raise Http404("Ref title not found.")

# get what other users viewed 
def getRecommendedIdTitles(ids):
  if ids and len(ids) > 0:
    body = {
      "query":{
        "terms":{
              "id": ids
           }
      }
    }
    response = doSearch(body)

    if len(response.hits) > 0:
      hit_list = []
      for hit in response.hits:
        hit_list.append({
          'id': str(hit.id),
          'title': hit.title
        })
      return hit_list
  # no match
  return []

def makeUpFilterList(filterList):
  # "1-传播,1-传播-1-媒体,1-传播-2-媒体测试,2-商业-1-贸易,3-民生,3-民生-1-社保,3-民生-2-社保测试"
  madeUpList = []
  fList = str.split(',')

  currentDomain = ''

  for item in fList:
    arr = item.split('-')
    currentDomain = arr[1]

    if len(arr) == 2:
      madeUpList.append(item)
    elif len(arr) == 4:
      madeUpList.append(item)

  return filterList


def getESQueryFromChecked(filterList, mustQuery):

  if len(filterList) == 0:
    return {"bool": {"must": mustQuery} }

  # "1-传播,1-传播-1-媒体,1-传播-2-媒体测试,2-商业,2-商业-1-贸易,3-民生,3-民生-1-社保,3-民生-2-社保测试"
  str = formatFilterList(filterList)
  fList = str.split(',')
  should = []
  must = []
  industry_should = []
  for item in fList:
    arr = item.split('-')

    if len(arr) == 2:
      if len(must) > 0:
        should.append({"bool": {"must": must, "should": industry_should, "minimum_should_match": 1}})
      must = []
      industry_should = []
      must.append({"term": {"domain" : arr[1]}})
    elif len(arr) == 4:
      industry_should.append({"term": {"industry" : arr[3]}})
  should.append({"bool": {"must": must, "should": industry_should , "minimum_should_match": 1}})

  return {"bool": {"must": mustQuery, "should": should, "minimum_should_match": 1 } }


def formatFilterList(filterList):
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

def doSearch(body):
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
  return response

# 404 page handler
def handler404(request, exception):
  return render(request, 'search/404.html', locals())

# the search API, handle the search request
# and get the filter tree 
def getree(request):
  start = time.clock()

  # get the posted keywords
  keyword = request.POST.get('keyword', '')
  pageNo = request.POST.get('pageNo', '')
  filterList = request.POST.get('filterList', '')
  orderby_val = int(request.POST.get('orderby', ''))

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
        # "type": "best_fields", 
        "fields": [ 
          "title^4", 
          "description^3", 
          "contents^3",
          "keyword^2",
          "industry^2",
          "topic^2",
          "source",
          "data_time"
        ], 
      }
    }
  else:
    # query for all the list 
    query = {
      "match_all":{}
    }

  boolBody = getESQueryFromChecked(filterList, query)

  body = {
    "query": boolBody,
    # "highlight" : { 
    #     "pre_tags" : ["<hl>"],
    #     "post_tags" : ["</hl>"],
    #     "fields" : { 
    #         "title": {}, 
    #         "description": {}
    #         # "contents": {}, 
    #         # "keywords": {}, 
    #         # "industry": {}, 
    #         # "topic": {}, 
    #         # "source": {}, 
    #         # "data_time": {} 
    #     }
    # },
    "from": start_from, 
    "size": 10, 
    "sort" : [
        { orderby[orderby_val] : {"order" : "desc"}},
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

  response = doSearch(body)

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
      'publish_time': dateFormat(hit.publish_time),
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
        # 'text': child.key + '(' + str(child.doc_count) + ')',
        # 'checked': child.doc_count > 0,
        'checked': False,
        'title': child.key,
        'count': child.doc_count
      })
    # parents nodes
    group_list.append({
      'key': ''.join([str(parent_index), "-", bucket.key]), 
      'count': bucket.doc_count,
      # 'text': bucket.key + '(' + str(bucket.doc_count) + ')',
      'title': bucket.key,
      'expand': False,
      'hasChildren':len(children) > 0,
      'children': children
    })

  end = time.clock()

  list_total = response.hits.total 
  # if list_total > settings.MAX_RESULTS_PAGES_DISPLAYED:
  #   list_total = settings.MAX_RESULTS_PAGES_DISPLAYED

  responseData = {
    'code': 200,
    'message': 'OK',
    'query': filterList,
    'body': body,
    'took': response.took,
    'time': end - start,
    'data': {
      'filter': group_list,
      'list': { 'data': hit_list, 'total': list_total }
      }
  }

  return JsonResponse(responseData)
  # return JsonResponse(response.to_dict())






