$(function() {
  var currentPage = 1;
  var order_by_latest = 1;

  var full_filter_dataset = [];
  var full_filter_dataset_map = {};
  var page_first_loaded = true;

  // search trigger methods
  $('#search-input').keydown(function(event) {
    if (event.which == 13) {
      event.preventDefault();

      currentPage = 1;
      doSearch();
    }
  });

  $('#search').bind('click', function() {

      currentPage = 1;
      doSearch();
  });

  // bind the tabs to change sorting order
  $('a[data-toggle="pill"]').on('shown.bs.tab', function (e) {
    var target = $(e.target).attr("id") // activated tab
    order_by_latest = (target == 'tab-latest') + 0;
    // console.log('tabs changed');
    doSearch();
  });

  // build the tree filter
  var tree = $('#tree').tree({
      primaryKey: 'key', // indicating which filed will be collected in method tree.getCheckedNodes()
      uiLibrary: 'bootstrap',
      iconsLibrary: 'fontawesome',
      autoLoad: false,
      lazyLoading: true,
      icons:{
        expand: '<i class="fa fa-angle-down"></i>',
        collapse: '<i class="fa fa-angle-up"></i>',
      },
      dataSource: [],
      checkboxes: true
  });

  // the search method 
  function doSearch(first_executed = false){
    $('#div-list-latest-items li').remove();
    $('.loading').show();
    $.ajax({
      type: "POST",
      url: "tree",
      dataType: 'json',
      data: { 
        keyword: $('#search-input').val().trim(),
        pageNo: currentPage,
        filterList: tree.getCheckedNodes(),
        orderby: order_by_latest
      }
    })
    .done(function(r){
      $('.loading').hide();
      if (r.code == 200){
        var list = r.data.list;
        var filter = r.data.filter;

        $('#result-number').text(list.total);

        // build the result list
        buildList(list);

        if (full_filter_dataset != []){
          filter = mergeDataSource(filter, full_filter_dataset);
        }

        // build the tree filter
        buildFilter(filter);


        if (page_first_loaded) {
          page_first_loaded = false;
          full_filter_dataset = filter;
          
          tree.checkAll();
          tree.on('checkboxChange', function (e, $node, record, state) {
            // alert('The new state of record ' + record.text + ' is ' + state);
            console.log(JSON.stringify(tree.getAll()));
          });
        }
        // console.log(JSON.parse(full_filter_dataset));
        // console.log(JSON.parse(filter));

        // rebuild the pagination according to the number of search results
        var pages = Math.ceil(list.total / 10);
        // currentPage = $pagination.twbsPagination('getCurrentPage');

        $pagination.twbsPagination('destroy');
        $pagination.twbsPagination($.extend({}, defaultOpts, {
          startPage: currentPage,
          totalPages: pages,
          onPageClick: function (event, pageNo) {
            currentPage = pageNo;
            doSearch();
          }
        }));
      } else {
        alert('error');
      }
    });
  }

  function mergeDataSource(filter, full_filter_dataset){
    console.log(filter);
    console.log(full_filter_dataset);

    return filter;
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
    var html = $.templates("#listTmpl").render(list);
    // $('#div-list-latest-items li').remove();
    $('#div-list-latest-items').append(html);
  }

  // build the tree-filter
  function buildFilter(filter){
    tree.render(filter);
  }

  // do empty-keyword-search on page load
  doSearch(true);

  // $("#publish_time").html($("#publish_time").text().replace("Z","").replace("T"," "))

});