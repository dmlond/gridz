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

        function cellChangeHandler(e, args) {
            var item_url = '/grid/'+ options.schema_id + '/' + options.grid_id + '/_entry/update'
            var changed_field = args.grid.getColumns()[args.cell].field
            var new_value = args.item[changed_field]
            var document = {
                'query': {'_id': args.item._id},
		'update' : {}
            };
            document['update'][changed_field] = new_value;
	    var resp = $.ajax({
		type: "POST",
		url: item_url,
		data: JSON.stringify({ 'document': document}),
                contentType: "application/json; charset=utf-8",
                success: function(data) {
		    args.grid.invalidateRow(args.row);
		    args.grid.render();
		}
	    });
        }

        function addRowHandler(e, args) {
            var item_url = '/grid/'+ options.schema_id + '/' + options.grid_id + '/_entry/create'
	    var resp = $.ajax({
		type: "POST",
		url: item_url,
		data: JSON.stringify({ 'document': args.item}),
                contentType: "application/json; charset=utf-8",
		dataType: "json",
                success: function(data) {
		    args.grid.invalidateAllRows();
		    options.uuids.push(data);
		    args.grid.updateRowCount();
		    args.grid.render();
		}
	    });
        }

	$.extend(this, {
	    // data provider methods
	    "getLength": getLength,
	    "getItem": getItem,
	    "getItemMetadata": getItemMetadata,
            "cellChangeHandler": cellChangeHandler,
	    "addRowHandler": addRowHandler
	});
    }
})(jQuery);
