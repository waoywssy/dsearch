$(function() {    
  // Handle the download event here, sending request to alter the downloads filed
  $("#btn-download-xls").bind('click', function(){
  	$.ajax({
      type: "POST",
      url: "/index/update",
      dataType: 'json',
      data: { 
        meta_id: $("#meta_id").val()
      }
    })
    .done(function(r) {
    	alert(r.message);
    	// TODO HERE

    });
  })

});