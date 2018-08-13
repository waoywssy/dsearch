$(function() {

  var currentPage = 1;
  var order_by_latest = 1; // 1: order by latest published; 0: order by readhot

  // var full_filter_dataset = [];
  // var full_filter_dataset_map = {};
  var page_first_loaded = true;
  var last_keyword = '';

  var expandStatus = []; // holding tree-nodes expanding status
  var checkedNodes = []; // holding tree-nodes checked status

  function resetPage() {
    currentPage = 1;
  }

  // search-on-enter trigger method
  $('#search-input').keydown(function(event) {
    if (event.which == 13) {
      event.preventDefault();

      resetPage();
      doSearch();
    }
  });

  // search-on-click trigger method
  $('#search').bind('click', function() {
      resetPage();
      doSearch();
  });

  // bind the tabs to switch sorting order
  $('a[data-toggle="pill"]').on('shown.bs.tab', function (e) {
    var target = $(e.target).attr("id") // activated tab
    order_by_latest = (target == 'tab-latest') + 0;

    doSearch();
  });

  // build the tree filter but datasource
  var tree = $('#tree').tree({
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

  // the search method 
  function doSearch(first_executed = false) {
    $('#div-list-latest-items li').remove();
    $('.loading').show();

    saveFilterStatus();

    $.ajax({
      type: "POST",
      url: "tree",
      dataType: 'json',
      data: { 
        keyword: $('#search-input').val().trim(),
        pageNo: currentPage,
        filterList: checkedNodes.join(),
        orderby: order_by_latest
      }
    })
    .done(function(r) {

      $('.loading').hide();

      if (r.code == 200){
        var list = r.data.list;
        var filter = r.data.filter;

        // build the result list
        buildList(list);

        if (page_first_loaded) {
          
          // build the tree filter
          buildFilter(filter);

          // the first time to load filters
          page_first_loaded = false;
          
          tree.checkAll();
        } else {
          var keyword = $('#search-input').val().trim();
          if (keyword == '' || last_keyword != keyword) {
            // build the tree filter
            buildFilter(filter);
            last_keyword = keyword;
          }
        }

        // rebuild the pagination according to the number of search results
        var pages = Math.ceil(list.total / 10);

        $pagination.twbsPagination('destroy');
        if (pages > 0){
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
  // build the result list 
  function buildList(list) {
    $('#result-number').text(list.total);

    if (list.total <= 10){
      resetPage();
    }

    var html = $.templates("#listTmpl").render(list);
    $('#div-list-latest-items').append(html);
  }

  // build the tree-filter
  function buildFilter(filter) {
    filter = setFilterTreeText(filter, false);

    tree.render(filter);

    restoreFilterStatus();
  }

  function setFilterTreeText(filter, useZero) {
    // display the checkbox label text with count
    for (var i = filter.length - 1; i >= 0; i--) {
      filter[i].text = getNodeText(filter[i], useZero);

      if (filter[i].hasChildren) {
        var nodes = filter[i].children;
        if (nodes) {
          for (var j = nodes.length - 1; j >= 0; j--) {
            nodes[j].text = getNodeText(nodes[j], useZero);
          }
        }
      }
    }
    return filter;
  }

  function getNodeText(node, useZero){
    return node.title + "(" + (useZero ? "0" : node.count)  + ")";
  }

  function saveFilterStatus() {
    // save the current expanding status, so it can be restored after ajax call
    $('#tree > ul > .list-group-item > div > span[data-role="expander"]').each(
      function(index){
        var key = $(this).parent().parent().attr('data-id');
        var val = $(this).attr('data-mode') == 'open'; // open, close
        expandStatus[key] = val;
      });

    // get the current checked nodes
    checkedNodes = tree.getCheckedNodes();
  }

  function restoreFilterStatus() {
    // expanding level one nodes
    for (var k in expandStatus){
      if (expandStatus.hasOwnProperty(k)) {
        if (expandStatus[k]){
          tree.expand(tree.getNodeById(k));
        }
      }
    }
  }

  // do the initial empty-keyword-search on page load
  doSearch(true);

  // $("#publish_time").html($("#publish_time").text().replace("Z","").replace("T"," "))
});