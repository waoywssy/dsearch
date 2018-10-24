$(function() {
  var MAX_PAGE_NUM = 1000;
  var ITEMS_PER_PAGE = 10;
  var ENTER_KEY_CODE = 13;
  var HTTP_STATUS_OK = 200;

  var TOP_CATEGORY_WEIGHT = {
    '政治经济':0,
    '社会民生':5,
    '生产能源':10,
    '科学技术':15,
    '教育文化':20,
    '国际交流':25,
  };

  var currentPage = 1;
  var order_by_latest = 1; // 1: order by latest published; 0: order by readhot

  var last_keyword = '';

  var expandStatus = []; // holding tree-nodes expanding status
  var checkedNodes = []; // holding tree-nodes checked status
  var checkedNodesDT = []; // holding data type tree-nodes checked status

  var last_checked_tree = null;

  function resetPage() {
    currentPage = 1;
  }

  // search-on-enter trigger method
  $('#search-input').keydown(function(event) {
    if (event.which == ENTER_KEY_CODE) {
      event.preventDefault();

      resetPage();
      doSearch(true);
    }
  });

  // search-on-click trigger method
  $('#search').bind('click', function() {
      resetPage();
      doSearch(true);
  });

  // stop events bubbling
  function stopHandler(event) {
      window.event ? window.event.cancelBubble=true : event.stopPropagation();  
  }

  // bind the tabs to switch sorting order
  $('a[data-toggle="pill"]').on('shown.bs.tab', function (e) {
    var target = $(e.target).attr("id"); // activated tab
    order_by_latest = (target == 'tab-latest') + 0;

    doSearch();
  });

  // build the tree filter but datasource
  var tree = _init_tree("tree");
  tree.on('onUpdate', function (e, $node, record, state) {
    last_checked_tree = tree;
     doSearch();
  });

  var tree_data_type = _init_tree("tree-data-type");
  tree_data_type.on('onUpdate', function (e, $node, record, state) {
    last_checked_tree = tree_data_type;
    doSearch();
  });

  // the search method 
  function doSearch(searchAll) {
    $('#div-list-latest-items li').remove();
    $('.loading').show();

    _saveFilterStatus();

    $.ajax({
      type: "POST",
      url: "tree",
      dataType: 'json',
      data: { 
        keyword: $('#search-input').val().trim(),
        pageNo: currentPage,
        filterList: searchAll ? '' : checkedNodes.join(),
        filterListDT: searchAll ? '' : checkedNodesDT.join(),
        orderby: order_by_latest
      }
    })
    .done(function(r) {
      $('.loading').hide();

      if (r.code == HTTP_STATUS_OK){
        var list = r.data.list;
        // build the result list
        buildList(list);

        if (searchAll) {
        // if (true){
          // build the tree filter
          buildFilter(tree, r.data.filter);
          buildFilter(tree_data_type, r.data.filter_dt);
        } else {
          if (last_checked_tree == tree){
            buildFilter(tree_data_type, r.data.filter_dt);
          } else {
            buildFilter(tree, r.data.filter);
          }
        }

        // rebuild the pagination according to the number of search results
        var pages = Math.ceil(list.total / ITEMS_PER_PAGE);
        pages = pages > MAX_PAGE_NUM ? MAX_PAGE_NUM : pages;

        $pagination.twbsPagination('destroy');
        if (pages > 0) {
          $pagination.twbsPagination($.extend({}, defaultOpts, {
            startPage: currentPage,
            totalPages: pages,
            onPageClick: function (event, pageNo) {
              currentPage = pageNo;
              doSearch();
            }
          }));
        }
        
      } else {
        alert('Network/Service error!');
      }
    });
  }

  // initialize the pagination module 
  var $pagination = $('#pagination');
  var defaultOpts = {
    totalPages: 1,
    visiblePages: 5,
    startPage: 1,
    prev: '&lsaquo;',
    next: '&rsaquo;',
    first: '«',
    last: '»',
    initiateStartPageClick: false
    // hideOnlyOnePage: true
  };
  $pagination.twbsPagination(defaultOpts);

  // overriding the default template delimiter in case of 
  // the confliction with django template deliveters
  $.views.settings.delimiters("<%", "%>");

  // do the initial empty-keyword-search on page load
  doSearch(true);
  
  // build the result list 
  function buildList(list) {
    $('#result-number').text(list.total);

    if (list.total <= ITEMS_PER_PAGE){
      resetPage();
    }

    var html = $.templates("#listTmpl").render(list);
    $('#div-list-latest-items').append(html);
  }

  // build the tree-filter
  function buildFilter(tree, filter) {
    // calculate top levevl category weight
    for (var i = 0; i < filter.length; i++){
      var weight = TOP_CATEGORY_WEIGHT[filter[i].title];
      weight = weight >= 0 ? weight: 9999;
      filter[i].weight = weight;
    }
    // sort filter by top level category weight
    filter.sort(function(a, b){
      var keyA = a.weight,
          keyB = b.weight;
      // Compare the 2 titles
      if(keyA < keyB) return -1;
      if(keyA > keyB) return 1;
      return 0;
    });

    filter = setFilterTreeText(filter, false);
    tree.render(filter);

    _restoreFilterStatus();
  }

  function setFilterTreeText(filter, useZero) {
    // display the checkbox label text with count
    for (var i = filter.length - 1; i >= 0; i--) {
      filter[i].text = _getNodeText(filter[i], useZero);

      if (filter[i].hasChildren) {
        var nodes = filter[i].children;
        if (nodes) {
          for (var j = nodes.length - 1; j >= 0; j--) {
            nodes[j].text = _getNodeText(nodes[j], useZero);
          }
        }
      }
    }
    return filter;
  }

  function _getNodeText(node, useZero){
    return node.title + "(" + (useZero ? "0" : node.count)  + ")";
  }

  function _saveFilterStatus() {
    // save the current expanding status, so it can be restored after ajax call
    $('#tree > ul > .list-group-item > div > span[data-role="expander"]').each(
      function(index){
        var key = $(this).parent().parent().attr('data-id');
        var val = $(this).attr('data-mode') == 'open'; // open, close
        expandStatus[key] = val;
      });

    // get the current checked nodes
    checkedNodes = tree.getCheckedNodes();
    checkedNodesDT = tree_data_type.getCheckedNodes();
  }

  function _restoreFilterStatus() {
    if (expandStatus){
      // expanding level one nodes
      for (var k in expandStatus){
        if (expandStatus.hasOwnProperty(k)) {
          if (expandStatus[k]){
            tree.expand(tree.getNodeById(k));
          }
        }
      }
    }
  }

  function _init_tree(tree_id, params){
    // build the tree filter but datasource
    return $('#' + tree_id).tree({
      primaryKey: 'key', // indicating which filed will be collected in method tree.getCheckedNodes()
      uiLibrary: 'bootstrap',
      iconsLibrary: 'fontawesome',
      hasChildrenField: 'hasChildren',
      autoLoad: false,
      lazyLoading: true,
      icons: {
        expand: '<i class="fa fa-angle-down"></i>',
        collapse: '<i class="fa fa-angle-up"></i>',
      },
      dataSource: [],
      checkboxes: true
    });
  }
});