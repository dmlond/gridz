(function ($) {
    $.extend(true, window, {
	GridView: GridView
    });

    function GridView(options) {
	var self = this;

	function getLength() {
	    return options.uuids.length; 
	}

	function getItem(i) {
            var item_url = '/grid/'+ options.schema_id + '/' + options.grid_id + '/_entry'
            var item;
	    var resp = $.ajax({
		type: "POST",
		url: item_url,
		data: JSON.stringify(options.uuids[i]),
                contentType: "application/json; charset=utf-8",
		dataType: "json",
                async: false,
                success: function(data) {
		    item = data;
		}
	    });
	    return item;
	}

	function getItemMetadata(i) {
	    return null;
	}

	$.extend(this, {
	    // data provider methods
	    "getLength": getLength,
	    "getItem": getItem,
	    "getItemMetadata": getItemMetadata
	});
    }
})(jQuery);
