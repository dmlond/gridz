(function ($) {
  function GridView(options) {
      var self = this;

      function getLength() {
	  return options.uuids.length; 
      }

      function getItem(i) {
          item_url = '/grid/'+ options.schema_id + '/' + options.grid_id + '/_entry'
          item = null;
          $.post(item_url,
                 {'_id': options.uuids[i]},
		 function(data) {
                     item = data;
                 },
                 "json"
		);
	  return item;
      }

      function getItemMetadata(i) {
	  return null;
      }
  }
})(jQuery);
