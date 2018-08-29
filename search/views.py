#coding:utf-8

from django.http import JsonResponse, Http404
from django.shortcuts import render
from search.suggestion import saveHistory
from search.until import getItem, getTree, updateDownload


# 404 page handler
def handler404(request, exception):
    return render(request, 'search/404.html', locals())

# Render the list page
def search(request):
    return render(request, 'search/list.html', {})

# Render the search-result detail page
def item(request, itemId):
    # call method
    request = saveHistory(request, itemId)
    params = getItem(itemId)
    if not params:
        raise Http404("Item not found.")
    return render(request, 'search/detail.html', params)

# the search API, handle the search request
# and get the filter tree 
def getree(request):
    # get the posted keywords
    keyword = request.POST.get('keyword', '')
    pageNo = request.POST.get('pageNo', '')
    filterList = request.POST.get('filterList', '')
    orderby_val = int(request.POST.get('orderby', ''))
    responseData = getTree(keyword, pageNo, filterList, orderby_val)
    if not responseData:
        raise Http404("Got exception in search.")
    return JsonResponse(responseData)

# Update downloads count
def update(request):
    meta_id = request.POST.get('meta_id', '')
    itemId = request.POST.get('id', '')
    responseData = updateDownload(meta_id, itemId)
    return JsonResponse(responseData)


