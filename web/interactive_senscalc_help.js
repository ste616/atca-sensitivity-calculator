require( [ 'dojo/query', 'dojo/hash', 'dojo/io-query', 'dojo/topic', 'dojo/NodeList-dom' ],
	 function(query, hash, ioQuery, topic) {

	     // Get the id to show from the address bar.
	     var showHelp = function() {
		 var o = ioQuery.queryToObject(hash());
		 for (var p in o) {
		     if (o.hasOwnProperty(p)) {
			 query("#" + p).removeClass('invisible');
		     }
		 }
	     };
	     // Do this on page load.
	     showHelp();

	     // Look out for changes in the hash.
	     topic.subscribe('/dojo/hashchange', function() {
		 // Hide all the help sections first.
		 query('.helpSection').addClass('invisible');
		 showHelp();
	     });
	 });
