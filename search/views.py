from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, A, FacetedSearch, TermsFacet, DateHistogramFacet
from elasticsearch_dsl.connections import connections

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
import time

from django.http import Http404

# Render the list page
def search(request):
	return render(request, 'search/list.html', {})

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
  response = doSearch(body)

  params = {}
  if len(response.hits) > 0:
    hit = response.hits[0]

    ref_id_title = ''
    if hit.ref_id:
      # get the title if ref_id exists
      ref_id_title = getRefIdTitle(hit.ref_id)

    params = {
      'id': hit.id, 
      'keywords': hit.keywords,
      'title': hit.title, 
      'contents': hit.contents, 
      'price': hit.price, 
      'level': hit.level, 
      'source': hit.source, 
      'data_time': hit.data_time, 
      'publish_time': hit.publish_time, 
      'readhot': hit.readhot,
      'downloads': hit.downloads,
      'ref_id': hit.ref_id,
      'ref_id_title': ref_id_title
    }
  else:
    raise Http404("Item not found.")

  return render(request, 'search/detail.html', params)

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



def doSearch(body):
  client = connections.create_connection(hosts=['http://localhost:9200'])
  s = Search(using=client, index="datastore", doc_type="doc")
  s = Search.from_dict(body)
  s = s.index("datastore")
  s = s.doc_type("doc")
  body = s.to_dict()
  response = s.execute()
  return response

# 404 page handler
def handler404(request, exception):
    return render(request, 'search/404.html', locals())

# get the filter tree 
def getree(request):
  start = time.clock()

  # get the posted keywords
  keyword = request.POST.get('keyword', '')
  pageNo = request.POST.get('pageNo', '')
  filterList = request.POST.get('filterList', '')  
  orderby_val = int(request.POST.get('orderby', ''))

  orderby = ["readhot", "publish_time"]

  start_from = (int(pageNo) - 1) * 10;

  query = {}
  if len(keyword.strip()) > 0:
    # query for keywords
    query = {
      "multi_match":{
        "query": keyword, 
        # "type": "best_fields", 
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
      "match_all":{}
    }

  body = {
    "query": query,
    "from": start_from, 
    "size": 10, 
    "sort" : [
        { orderby[orderby_val] : {"order" : "desc"}},
        "_score"
    ],
    "aggs": {
      "by_domain_industry": {
        "terms": {
          "field": "domain.keyword",
          "size": 999,
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
    hit_list.append({
      'id': hit.id, 
      # 'doc_id': hit.meta.id,
      'title': hit.title, 
      'description': hit.description, 
      'source': hit.source, 
      'data_time': hit.data_time, 
      'publish_time': hit.publish_time, 
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
        # 'checked': False,
        'key': ''.join([str(parent_index), "-", str(child_index), "-", child.key]), 
        'count': child.doc_count,
        'text': child.key + '(' + str(child.doc_count) + ')',
        'checked': True,
      })
    group_list.append({
      # 'checked': False,
      'key': ''.join([str(parent_index), "-", bucket.key]), 
      'count': bucket.doc_count,
      'text': bucket.key + '(' + str(bucket.doc_count) + ')',
      'checked': True,
      'hasChildren':len(children) > 0,
      'children': children
    })

  end = time.clock()

  responseData = {
    'code': 200,
    'message': 'OK',
    'took': response.took,
    'time': end - start,
    'data': {
      'filter': group_list,
      'list': {'data': hit_list, 'total': response.hits.total}
      }
  }

  return JsonResponse(responseData)
  # return JsonResponse(response.to_dict())



def json(request):
  # get the posted keywords
  keyword = request.POST.get('keyword', '')
  pageNo = request.POST.get('pageNo', '')
  filterList = request.POST.get('filterList', '')
  orderby = request.POST.get('orderby', '')

  client = Elasticsearch()
  s = Search(using=client, index="search_engine_data").query("match", domain=keyword).extra(size=10)

  # s = Search().sort(
  #   'category',
  #   '-title',
  #   {"lines": {"order": "asc", "mode": "avg"}}
  # )

  # 按照title升序，内容降序排列
  # s = s.sort('jks_title', '-jks_content')
  # for pagination; from value is 10, size value is 10
  s = s[0:10]

  response = s.execute()

  list = []
  for hit in response:
    list.append({'title': hit.jks_title, 'content': hit.jks_content})

  postdata = ''
  if request.method == "GET":
    postdata = request.GET.get("name", "")

  responseData = {
    'code': 200,
    'message': 'OK',
    'data': list,
    'total': s.count(),
    'postdata': postdata
  }
  return JsonResponse(responseData)








