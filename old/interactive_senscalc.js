require( [ 'dojo/dom', 'dojo/dom-attr', 'dojo/on', 'dojo/query', 'dojo/store/Memory',
	   'dijit/form/ComboBox', 'dojo/dom-class', 'dojo/_base/fx', 'dojo/dom-style',
	   'dojo/fx', 'dojo/dom-construct', 'dojo/request/xhr', 'atnf/base',
	   'dojo/dom-geometry',
	   'dojo/NodeList-manipulate', 'dojo/NodeList-dom', 'dojo/domReady!' ],
	 function(dom, domAttr, on, query, Memory, ComboBox, domClass, fx, domStyle, 
		  coreFx, domConstruct, xhr, atnf, domGeom) {

	     var linkedElements = [
		 // Text input elements.
		 [ 'data-cabb-centralfreq', 'interactive-continuum-cabb-centralfreq' ],
		 [ 'data-cabb-zoomfreq', 'interactive-cabb-spectralfreq' ],
		 [ 'data-declination', 'interactive-declination' ],
		 [ 'data-elevation-limit', 'interactive-elevation-limit' ],
		 [ 'data-hourangle-limit', 'interactive-hourangle-limit' ],
		 [ 'data-nzooms', 'interactive-nzooms' ],
		 [ 'data-smoothing', 'interactive-smoothing' ],
		 [ 'data-remove-edge', 'interactive-remove-edge' ],
		 [ 'data-integration', 'interactive-integration' ],
		 [ 'data-sensitivity', 'interactive-sensitivity' ],
		 // Radio buttons.
		 [ 'data-array', 'interactive-array' ],
		 [ 'data-image-weight', 'interactive-image-weight', 
		   'interactive-cube-weight' ],
		 [ 'data-required', 'interactive-required' ],
		 [ 'data-sensitivity-units', 'interactive-sensitivity-units' ],
		 [ 'data-sensitivity-mode', 'interactive-sensitivity-mode' ],
		 [ 'data-sensitivity-weather', 'interactive-sensitivity-weather' ],
		 [ 'data-cabb-mode', 'interactive-cabb-mode' ],
		 // Checkboxes.
		 [ 'data-include-ca06', 'interactive-include-ca06' ],
		 [ 'data-remove-birdies', 'interactive-remove-birdies' ],
		 [ 'data-remove-rfi', 'interactive-remove-rfi' ]
	     ];
	     var elementDefaults = [
		 // Text input elements.
		 '', '', '-30', '12', '6', '1', '1', '0', '720', '1',
		 // Radio buttons.
		 '6km', 'N', 'Integration', 'mJy/beam', 'continuum', 'good', 'CFB1M',
		 // Checkboxes.
		 true, true, true
	     ];

	     // Get the band name from the frequency.
	     var bandName = function(freq) {
		 if (freq >= 600 && freq <= 3424) {
		     return '16cm';
		 } else if (freq >=3904 && freq <= 11952) {
		     return '4cm';
		 } else if (freq >= 14976 && freq <= 26024) {
		     return '15mm';
		 } else if (freq >= 28976 && freq <= 51024) {
		     return '7mm';
		 } else if (freq >= 83976 && freq <= 106024) {
		     return '3mm';
		 } else {
		     return null;
		 }
	     };

	     var bandContinuumFrequencies = {
		 '16cm': [ 2100 ],
		 '4cm': [ 5500, 9000 ],
		 '15mm': [ 17000, 19000 ],
		 '7mm': [ 33000, 35000, 43000, 45000 ],
		 '3mm': [ 93000, 95000 ]
	     };

	     var showAlert = function(alertId) {
		 if (dom.byId(alertId)) {
		     domClass.add(alertId, 'md-show');
		 }
	     };

	     query('.md-close').on('click', function(e) {
		 query('.md-modal').removeClass('md-show');
	     });

	     var errorChecks = function(cId) {
		 // Error checking on some values.
		 var myVal = domAttr.get(cId, 'value');
		 if (cId === 'data-nzooms' ||
		     cId === 'interactive-nzooms') {
		     if (myVal < 1 || myVal > 16) {
			 myVal = (myVal < 1) ? 1 : 16;
			 domAttr.set(cId, 'value', myVal);
			 showAlert('modal-error-nzooms');
			 return false;
		     }
		 }
		 if (cId === 'data-elevation-limit' ||
		     cId === 'interactive-elevation-limit') {
		     if (myVal < 12 || myVal > 80) {
			 myVal = (myVal < 12) ? 12 : 80;
			 domAttr.set(cId, 'value', myVal);
			 showAlert('modal-error-elevation');
			 return false;
		     }
		 }
		 if (cId === 'data-cabb-centralfreq' ||
		     cId === 'interactive-continuum-cabb-centralfreq') {
		     if (!bandName(myVal)) {
			 myVal = '';
			 domAttr.set(cId, 'value', myVal);
			 showAlert('modal-error-cabbfreq');
			 return false;
		     }
		 }
		 if (cId === 'data-declination' ||
		     cId === 'interactive-declination') {
		     if (myVal < -90 || myVal > 48) {
			 myVal = (myVal < -90) ? -90 : 48;
			 domAttr.set(cId, 'value', myVal);
			 showAlert('modal-error-declination');
			 return false;
		     }
		 }
		 
		 return true;
	     };

	     /**
		A routine that will force changes in one set of elements
		based on another set. 
	     **/
	     var linker = function(evtObj) {
		 var myId = evtObj.target.id;
		 var myName = evtObj.target.name;
		 // Find the partner(s) of the element that has changed.
		 for (var i = 0; i < linkedElements.length; i++) {
		     if (linkedElements[i].indexOf(myId) >= 0) {
			 if (evtObj.target.type === "checkbox") {
			     var myVal = evtObj.target.checked;
			     for (var j = 0; j < linkedElements[i].length; j++) {
				 if (myId != linkedElements[i][j]) {
				     dom.byId(linkedElements[i][j]).checked = myVal;
				 }
			     }
			 } else {
			     var myVal = domAttr.get(myId, 'value');
			     errorChecks(myId);
			     for (var j = 0; j < linkedElements[i].length; j++) {
				 if (myId != linkedElements[i][j]) {
				     domAttr.set(linkedElements[i][j], 'value', myVal);
				 }
			     }
			 }
		     } else if (linkedElements[i].indexOf(myName) >= 0) {
			 var myVal = query('[name="' + myName + '"]:checked').val();
			 for (var j = 0; j < linkedElements[i].length; j++) {
			     if (myName != linkedElements[i][j]) {
				 query('[name="' + linkedElements[i][j] + '"]').val(myVal);
			     }
			 }
		     }
		 }
		 // Do special things for some events, and some error checking.
		 if (myName === 'interactive-required' ||
		     myName === 'data-required') {
		     var myVal = query('[name="' + myName +'"]:checked').val();
		     if (myVal === 'Integration') {
			 panelOrder['panel-calculation-mode']['next'] =
			     panelOrder['panel-calculate-button']['previous'] =
			     'panel-integration-time';
		     } else if (myVal === 'Sensitivity') {
			 panelOrder['panel-calculation-mode']['next'] =
			     panelOrder['panel-calculate-button']['previous'] =
			     'panel-sensitivity-required';
		     }
		 }
		 if (myId === 'data-cabb-zoomfreq' ||
		     myId === 'interactive-cabb-spectralfreq') {
		     // We automatically set a continuum frequency if required.
		     var cabbFreq = domAttr.get('data-cabb-centralfreq', 'value');
		     var zoomFreq = domAttr.get('data-cabb-zoomfreq', 'value');
		     if (zoomFreq === '') {
			 return;
		     }
		     zoomFreq = parseInt(zoomFreq);
		     if (cabbFreq !== '' &&
			 Math.abs(parseInt(cabbFreq) - zoomFreq) < 960) {
			 return;
		     }
		     var bestFreq = 0;
		     var band = bandName(zoomFreq);
		     if (!band) {
			 // Oops, invalid frequency!
			 showAlert('modal-error-zoomfreq');
			 return;
		     }
		     var cb = 0;
		     // Try to set the continuum frequency to one of the
		     // recommended values.
		     bestFreq = bandContinuumFrequencies[band][cb];
		     while(Math.abs(bestFreq - zoomFreq) > 960 &&
			   cb < (bandContinuumFrequencies[band].length - 1)) {
			 cb++;
			 bestFreq = bandContinuumFrequencies[band][cb];
		     }
		     // Can't use a recommended frequency, simply use the zoom
		     // frequency as the continuum frequency.
		     if (Math.abs(bestFreq - zoomFreq) > 960) {
			 bestFreq = zoomFreq;
		     }
		     // If we lie in the 7mm dead zone, adjust as required.
		     if (bestFreq > 40000 && bestFreq < 40500) {
			 bestFreq = 40000;
		     } else if (bestFreq >= 40500 && bestFreq < 41000) {
			 bestFreq = 41000;
		     }
		     
		     domAttr.set('data-cabb-centralfreq', 'value', bestFreq);
		     domAttr.set('interactive-continuum-cabb-centralfreq', 
				 'value', bestFreq);
		 }
	     };
	     
	     // Enable the linkages.
	     for (var i = 0; i < linkedElements.length; i++) {
		 for (var j = 0; j < linkedElements[i].length; j++) {
		     if (dom.byId(linkedElements[i][j])) {
			 on(dom.byId(linkedElements[i][j]), 'change', linker);
		     } else {
			 query('[name="' + linkedElements[i][j] + '"]').
			     on('click', linker);
		     }
		 }
	     }

	     // Make the rest frequency input a special thing.
	     var lineFrequencies = new Memory({
		 'data': [
		     { 'name': 'HI = 1.420405752', 'value': 1.420405752 },
		     { 'name': 'OH = 1.6122310', 'value': 1.6122310 },
		     { 'name': 'OH = 1.6654018', 'value': 1.6654018 },
		     { 'name': 'OH = 1.6673590', 'value': 1.6673590 },
		     { 'name': 'OH = 1.7205300', 'value': 1.7205300 },
		     { 'name': 'H2CO = 4.829660', 'value': 4.829660 },
		     { 'name': 'CH3OH = 6.668518', 'value': 6.668518 },
		     { 'name': 'HC3N = 9.098332', 'value': 9.098332 },
		     { 'name': 'CH3OH = 12.178593', 'value': 12.178593 },
		     { 'name': 'H2CO = 14.488490', 'value': 14.488490 },
		     { 'name': 'C3H2 = 18.343145', 'value': 18.343145 },
		     { 'name': 'H2O = 22.23507985', 'value': 22.23507985 },
		     { 'name': 'NH3 = 23.694506', 'value': 23.694506 },
		     { 'name': 'NH3 = 23.722634', 'value': 23.722634 },
		     { 'name': 'NH3 = 23.870130', 'value': 23.870130 },
		     { 'name': 'SiO = 42.820570', 'value': 42.820570 },
		     { 'name': 'SiO = 43.122090', 'value': 43.122090 },
		     { 'name': 'SiO = 43.423853', 'value': 43.423853 },
		     { 'name': 'CS = 48.990964', 'value': 48.990964 },
		     { 'name': 'DCO+ = 72.039331', 'value': 72.039331 },
		     { 'name': 'SiO = 85.640456', 'value': 85.640456 },
		     { 'name': 'SiO = 86.243442', 'value': 86.243442 },
		     { 'name': 'H13CO+ = 86.754294', 'value': 86.754294 },
		     { 'name': 'SiO = 86.846998', 'value': 86.846998 },
		     { 'name': 'HCN = 88.641847', 'value': 88.641847 },
		     { 'name': 'HCO+ = 89.188518', 'value': 89.188518 },
		     { 'name': 'HNC = 90.663574', 'value': 90.663574 },
		     { 'name': 'N2H+ = 93.173809', 'value': 93.173809 },
		     { 'name': 'CS = 97.980968', 'value': 97.980968 },
		     { 'name': 'C18O = 109.782182', 'value': 109.782182 },
		     { 'name': '13CO = 110.20137', 'value': 110.20137 },
		     { 'name': 'CO = 115.271203', 'value': 115.271203 }
		 ]
	     });
	     var freqBox1 = new ComboBox({
		 'id': 'data-rest-frequency',
		 'name': 'data-rest-frequency',
		 'value': '',
		 'store': lineFrequencies,
		 'searchAttr': 'name'
	     }, 'data-rest-frequency' );
	     var freqBox2 = new ComboBox({
		 'id': 'interactive-line-frequency',
		 'name': 'interactive-line-frequency',
		 'value': '',
		 'store': lineFrequencies,
		 'searchAttr': 'name'
	     }, 'interactive-line-frequency' );
	     // A routine to keep these in sync.
	     var restSync = function(chValue) {
		 freqBox1.set('value', chValue);
		 freqBox2.set('value', chValue);
	     };
	     freqBox1.on('change', restSync);
	     freqBox2.on('change', restSync);

	     // Make the band select buttons change the frequencies.
	     var changeContinuumFrequencies = function(evtObj) {
		 var band = /^bandselect_(.*)$/.exec(evtObj.target.id);
		 var currFreq = domAttr.get('interactive-continuum-cabb-centralfreq',
					    'value');
		 var freqIndex = bandContinuumFrequencies[band[1]].
		     indexOf(parseInt(currFreq));
		 if (freqIndex < 0 ||
		     freqIndex === (bandContinuumFrequencies[band[1]].length - 1)) {
		     freqIndex = 0;
		 } else {
		     freqIndex++;
		 }
		 domAttr.set('interactive-continuum-cabb-centralfreq', 'value',
			     bandContinuumFrequencies[band[1]][freqIndex]);
		 domAttr.set('data-cabb-centralfreq', 'value',
			     bandContinuumFrequencies[band[1]][freqIndex]);
	     };
	     for (var b in bandContinuumFrequencies) {
		 if (bandContinuumFrequencies.hasOwnProperty(b)) {
		     on(dom.byId("bandselect_" + b), 'click',
			changeContinuumFrequencies);
		 }
	     }

	     // Set up the interview functionality.
	     var panelShown = null;
	     var firstPanel = 'panel-mode-choice';
	     var calculatorMode = '';
	     var panelOrder = {
		 'panel-mode-choice': {
		     'next': '', 'previous': ''
		 }, 'panel-continuum-frequency': {
		     'next': 'panel-array-configuration', 
		     'previous': 'panel-mode-choice'
		 }, 'panel-spectral-frequency': {
		     'next': 'panel-array-configuration', 
		     'previous': 'panel-mode-choice'
		 }, 'panel-array-configuration': {
		     'next': 'panel-cabb-configuration', 'previous': ''
		 }, 'panel-cabb-configuration': {
		     'next': 'panel-source-properties', 
		     'previous': 'panel-array-configuration'
		 }, 'panel-source-properties': {
		     'next': 'panel-observation-properties', 
		     'previous': 'panel-cabb-configuration',
		 }, 'panel-observation-properties': {
		     'next': '', 'previous': 'panel-source-properties'
		 }, 'panel-continuum-imaging': {
		     'next': 'panel-flagging', 
		     'previous': 'panel-observation-properties'
		 }, 'panel-spectral-imaging': {
		     'next': 'panel-flagging', 
		     'previous': 'panel-observation-properties'
		 }, 'panel-flagging': {
		     // 'next': 'panel-calculation-mode', 'previous': ''
		     'next': 'panel-integration-time',
		     'previous': ''
		 }, 'panel-calculation-mode': {
		     'next': 'panel-integration-time', 
		     'previous': 'panel-flagging'
		 }, 'panel-integration-time': {
		     'next': 'panel-calculate-button', 
		     // 'previous': 'panel-calculation-mode'
		     'previous': 'panel-flagging'
		 }, 'panel-sensitivity-required': {
		     'next': 'panel-calculate-button', 
		     // 'previous': 'panel-calculation-mode'
		     'previous': 'panel-flagging'
		 }, 'panel-calculate-button': {
		     'next': '', 'previous': 'panel-integration-time'
		 }
	     };

	     var interviewDeterminePanel = function(currentPanel, type) {
		 if (!currentPanel) {
		     // No currently selected panel, return the default.
		     return(firstPanel);
		 }

		 if (type === 'nextLink' || type === 'previousLink') {
		     if (currentPanel === firstPanel) {
			 return false;
		     }
		     if (typeof panelOrder[currentPanel] === 'undefined') {
			 return false;
		     }
		     type = (type === 'nextLink') ? 'next' : 'previous';
		     if (typeof panelOrder[currentPanel][type] === 'undefined' ||
			 panelOrder[currentPanel][type] === '') {
			 return false;
		     }
		     return true;
		 }

		 if (type === 'next' || type === 'previous') {
		     if (typeof panelOrder[currentPanel] === 'undefined') {
			 return null;
		     }
		     if (typeof panelOrder[currentPanel][type] === 'undefined' ||
			 panelOrder[currentPanel][type] === '') {
			 return null;
		     }
		     return panelOrder[currentPanel][type];
		 }

		 // This is the default to make it easier to debug.
		 return(null);
	     };

	     // The panel switching routine.
	     var interviewSwitchPanel = function(panelId) {
		 // Set up an animation chain.
		 var animChain = [];
		 var animDuration = 100; // In ms.
		 // Hide the current panel.
		 if (panelShown && dom.byId(panelShown)) {
		     animChain.push(fx.fadeOut({
			 'node': panelShown,
			 'duration': animDuration,
			 'onEnd': function() {
			     domClass.add(panelShown, 'invisible');
			     domClass.add(panelShown, 'invisible');
			 }
		     }));
		 }
		 // Display the panel if we can find it.
		 if (panelId && dom.byId(panelId)) {
		     // domClass.remove(panelId, 'invisible');
		     animChain.push(fx.fadeIn({
			 'node': panelId,
			 'duration': animDuration,
			 'beforeBegin': function() {
			     domClass.remove(panelId, 'invisible');
			     panelShown = panelId;
			 }
		     }));
		 }

		 // Set up the previous and next buttons.
		 query('.navigation', panelId).orphan();
		 var prevPanel = interviewDeterminePanel(panelId, 'previousLink');
		 var nextPanel = interviewDeterminePanel(panelId, 'nextLink');
		 if (prevPanel || nextPanel) {
		     var navDiv = domConstruct.create('div', {
			 'class': 'navigation'
		     }, panelId);
		     if (prevPanel) {
			 var prevDiv = domConstruct.create('div', {
			     'class': 'navigation-previous',
			     'innerHTML': '<<< Previous Question'
			 }, navDiv);
			 on(prevDiv, 'click', function() {
			     interviewGotoPanel('previous');
			 });
		     }
		     if (nextPanel) {
			 var nextDiv = domConstruct.create('div', {
			     'class': 'navigation-next',
			     'innerHTML': 'Next Question >>>'
			 }, navDiv);
			 on(nextDiv, 'click', function() {
			     interviewGotoPanel('next');
			 });
		     }
		     
		 }
		 

		 // Play the animation.
		 if (animChain.length > 0) {
		     coreFx.chain(animChain).play();
		 }
		 
	     };

	     // Go to another panel.
	     var interviewGotoPanel = function(direction) {
		 interviewSwitchPanel(interviewDeterminePanel(panelShown, direction));
	     };
	     
	     // Connect the mode buttons.
	     on(dom.byId('mode-button-continuum'), 'click',
		function(e) {
		    panelOrder['panel-mode-choice']['next'] =
			panelOrder['panel-array-configuration']['previous'] =
			'panel-continuum-frequency';
		    panelOrder['panel-observation-properties']['next'] =
			panelOrder['panel-flagging']['previous'] =
			'panel-continuum-imaging';
		    interviewGotoPanel('next');
		});
	     on(dom.byId('mode-button-spectralline'), 'click',
		function(e) {
		    panelOrder['panel-mode-choice']['next'] =
			panelOrder['panel-array-configuration']['previous'] =
			'panel-spectral-frequency';
		    panelOrder['panel-observation-properties']['next'] =
			panelOrder['panel-flagging']['previous'] =
			'panel-spectral-imaging';
		    interviewGotoPanel('next');
		});

	     // Hide all the panels and start the interview.
	     query('.interview-panel').addClass('invisible transparent');
	     interviewSwitchPanel(interviewDeterminePanel(null, null));

	     // The routine to fill the results page.
	     var resultsIds = {
		 // Continuum summary panels.
		 'results-summary-continuum-integration-time':
		 [ 'source_imaging', 'integration_time' ],
		 'results-summary-continuum-integration-centralfreq':
		 [ 'parameters', 'central_frequency' ],
		 'results-summary-continuum-integration-weighting':
		 [ 'source_imaging', 'weighting_scheme' ],
		 'results-summary-continuum-integration-surfacebrightness':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   'continuum', 0 ],
		 'results-summary-continuum-integration-sensitivity':
		 [ 'sensitivities', 'rms_noise_level', 'continuum', 0 ],
		 'results-summary-continuum-sensitivity-centralfreq':
		 [ 'parameters', 'central_frequency' ],
		 'results-summary-continuum-sensitivity-weighting':
		 [ 'source_imaging', 'weighting_scheme' ],
		 'results-summary-continuum-sensitivity-surfacebrightness':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   'continuum', 0 ],
		 'results-summary-continuum-sensitivity-sensitivity':
		 [ 'sensitivities', 'rms_noise_level', 'continuum', 0 ],
		 'results-summary-continuum-sensitivity-time':
		 [ 'source_imaging', 'integration_time' ],

		 // Spectral line summary panel.
		 'results-summary-spectral-integration-time':
		 [ 'source_imaging', 'integration_time' ],
		 'results-summary-spectral-integration-centralfreq':
		 [ 'parameters', 'central_frequency' ],
		 'results-summary-spectral-integration-weighting':
		 [ 'source_imaging', 'weighting_scheme' ],
		 'results-summary-spectral-integration-channelwidth':
		 [ 'continuum', 'spectral_channel_resolution'],
		 'results-summary-spectral-integration-surfacebrightness':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   'spectral', 0 ],
		 'results-summary-spectral-integration-sensitivity':
		 [ 'sensitivities', 'rms_noise_level', 'spectral', 0 ],
		 'results-summary-spectral-sensitivity-centralfreq':
		 [ 'parameters', 'central_frequency' ],
		 'results-summary-spectral-sensitivity-weighting':
		 [ 'source_imaging', 'weighting_scheme' ],
		 'results-summary-spectral-sensitivity-channelwidth':
		 [ 'continuum', 'spectral_channel_resolution'],
		 'results-summary-spectral-sensitivity-surfacebrightness':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   'spectral', 0 ],
		 'results-summary-spectral-sensitivity-sensitivity':
		 [ 'sensitivities', 'rms_noise_level', 'spectral', 0 ],
		 'results-summary-spectral-sensitivity-time':
		 [ 'source_imaging', 'integration_time' ],
		 

		 // Zoom band summary panel.
		 'results-summary-zoom-integration-time':
		 [ 'source_imaging', 'integration_time' ],
		 'results-summary-zoom-integration-nzooms':
		 [ [ 'specific_zoom', 'zoom' ], 'n_zooms' ],
		 'results-summary-zoom-integration-centralfreq':
		 [ 'parameters', [ 'zoom_frequency', 'central_frequency' ] ],
		 'results-summary-zoom-integration-weighting':
		 [ 'source_imaging', 'weighting_scheme' ],
		 'results-summary-zoom-integration-channelwidth':
		 [ [ 'specific_zoom', 'zoom' ], 'spectral_channel_resolution'],
		 'results-summary-zoom-integration-surfacebrightness':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   [ 'specific_zoom', 'zoom' ], 0 ],
		 'results-summary-zoom-integration-sensitivity':
		 [ 'sensitivities', 'rms_noise_level', 
		   [ 'specific_zoom', 'zoom' ], 0 ],
		 'results-summary-zoom-sensitivity-nzooms':
		 [ [ 'specific_zoom', 'zoom' ], 'n_zooms' ],
		 'results-summary-zoom-sensitivity-centralfreq':
		 [ 'parameters', 'zoom_frequency' ],
		 'results-summary-zoom-sensitivity-weighting':
		 [ 'source_imaging', 'weighting_scheme' ],
		 'results-summary-zoom-sensitivity-channelwidth':
		 [ [ 'specific_zoom', 'zoom' ], 'spectral_channel_resolution'],
		 'results-summary-zoom-sensitivity-surfacebrightness':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   [ 'specific_zoom', 'zoom' ], 0 ],
		 'results-summary-zoom-sensitivity-sensitivity':
		 [ 'sensitivities', 'rms_noise_level',
		   [ 'specific_zoom', 'zoom' ], 0 ],
		 'results-summary-zoom-sensitivity-time':
		 [ 'source_imaging', 'integration_time' ],

		 // Array Information panel.
		 'results-array-nantenna':
		 [ 'parameters', 'n_antenna' ],
		 'results-array-nbaselines':
		 [ 'parameters', 'n_baselines' ],
		 'results-array-longestbaseline':
		 [ 'parameters', 'configuration' ],
		 'results-array-efficiency':
		 [ 'parameters', 'antenna_efficiency' ],
		 'results-array-systemtemperature-goodweather':
		 [ 'sensitivities', 'system_temperature', 0 ],
		 'results-array-systemtemperature-averageweather':
		 [ 'sensitivities', 'system_temperature', 1 ],
		 'results-array-systemtemperature-poorweather':
		 [ 'sensitivities', 'system_temperature', 2 ],
		 'results-array-antennasensitivity-goodweather':
		 [ 'sensitivities', 'antenna_sensitivity', 0 ],
		 'results-array-antennasensitivity-averageweather':
		 [ 'sensitivities', 'antenna_sensitivity', 1 ],
		 'results-array-antennasensitivity-poorweather':
		 [ 'sensitivities', 'antenna_sensitivity', 2 ],
		 'results-array-arraysensitivity-goodweather':
		 [ 'sensitivities', 'array_sensitivity', 0 ],
		 'results-array-arraysensitivity-averageweather':
		 [ 'sensitivities', 'array_sensitivity', 1 ],
		 'results-array-arraysensitivity-poorweather':
		 [ 'sensitivities', 'array_sensitivity', 2 ],

		 // Continuum Information panel.
		 'results-continuum-weighting':
		 [ 'source_imaging', 'weighting_scheme' ],
		 'results-continuum-weightingfactor':
		 [ 'source_imaging', 'weighting_factor' ],
		 'results-continuum-primarybeam':
		 [ 'source_imaging', 'field_of_view' ],
		 'results-continuum-synthesisedbeam':
		 [ 'source_imaging', 'synthesised_beam_size' ],
		 'results-continuum-synthesisedbeambest':
		 [ 'source_imaging', 'synthesised_beam_size_best' ],
		 'results-continuum-centralfrequency':
		 [ 'parameters', 'central_frequency' ],
		 'results-continuum-effectivebandwidth':
		 [ 'continuum', 'effective_bandwidth' ],
		 'results-continuum-rmsnoiselevel-goodweather':
		 [ 'sensitivities', 'rms_noise_level', 'continuum', 0 ],
		 'results-continuum-rmsnoiselevel-averageweather':
		 [ 'sensitivities', 'rms_noise_level', 'continuum', 1 ],
		 'results-continuum-rmsnoiselevel-poorweather':
		 [ 'sensitivities', 'rms_noise_level', 'continuum', 2 ],
		 'results-continuum-brightnesstemperature-goodweather':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   'continuum', 0 ],
		 'results-continuum-brightnesstemperature-averageweather':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   'continuum', 1 ],
		 'results-continuum-brightnesstemperature-poorweather':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   'continuum', 2 ],

		 // Spectral Information panel.
		 'results-spectral-weighting':
		 [ 'source_imaging', 'weighting_scheme' ],
		 'results-spectral-weightingfactor':
		 [ 'source_imaging', 'weighting_factor' ],
		 'results-spectral-primarybeam':
		 [ 'source_imaging', 'field_of_view' ],
		 'results-spectral-synthesisedbeam':
		 [ 'source_imaging', 'synthesised_beam_size' ],
		 'results-spectral-centralfrequency':
		 [ 'parameters', 'central_frequency' ],
		 'results-spectral-effectivebandwidth':
		 [ 'continuum', 'effective_bandwidth' ],
		 'results-spectral-frequencyresolution':
		 [ 'continuum', 'channel_bandwidth' ],
		 'results-spectral-velocitywidth':
		 [ 'continuum', 'spectral_bandwidth' ],
		 'results-spectral-velocityresolution':
		 [ 'continuum', 'spectral_channel_resolution' ],
		 'results-spectral-restfrequency':
		 [ 'parameters', 'reference_rest_frequency' ],
		 'results-spectral-rmsnoiselevel-goodweather':
		 [ 'sensitivities', 'rms_noise_level', 'spectral', 0 ],
		 'results-spectral-rmsnoiselevel-averageweather':
		 [ 'sensitivities', 'rms_noise_level', 'spectral', 1 ],
		 'results-spectral-rmsnoiselevel-poorweather':
		 [ 'sensitivities', 'rms_noise_level', 'spectral', 2 ],
		 'results-spectral-brightnesstemperature-goodweather':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   'spectral', 0 ],
		 'results-spectral-brightnesstemperature-averageweather':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   'spectral', 1 ],
		 'results-spectral-brightnesstemperature-poorweather':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   'spectral', 2 ],

		 // Zoom Information panel.
		 'results-zoom-weighting':
		 [ 'source_imaging', 'weighting_scheme' ],
		 'results-zoom-weightingfactor':
		 [ 'source_imaging', 'weighting_factor' ],
		 'results-zoom-primarybeam':
		 [ 'source_imaging', [ 'field_of_view_zoom', 'field_of_view' ] ],
		 'results-zoom-synthesisedbeam':
		 [ 'source_imaging', [ 'synthesised_beam_size_zoom', 
				       'synthesised_beam_size' ] ],
		 'results-zoom-centralfrequency':
		 [ 'parameters', [ 'zoom_frequency', 'central_frequency' ] ],
		 'results-zoom-effectivebandwidth':
		 [ [ 'specific_zoom', 'zoom' ], 'zoom_total_bandwidth' ],
		 'results-zoom-frequencyresolution':
		 [ [ 'specific_zoom', 'zoom' ], 'zoom_channel_bandwidth' ],
		 'results-zoom-cubeplanes':
		 [ [ 'specific_zoom', 'zoom' ], 'n_channels' ],
		 'results-zoom-velocitywidth':
		 [ [ 'specific_zoom', 'zoom' ], 'zoom_total_spectral_bandwidth' ],
		 'results-zoom-velocityresolution':
		 [ [ 'specific_zoom', 'zoom' ], 'spectral_channel_resolution' ],
		 'results-zoom-restfrequency':
		 [ 'parameters', 'reference_rest_frequency' ],
		 'results-zoom-rmsnoiselevel-goodweather':
		 [ 'sensitivities', 'rms_noise_level', 
		   [ 'specific_zoom', 'zoom' ], 0 ],
		 'results-zoom-rmsnoiselevel-averageweather':
		 [ 'sensitivities', 'rms_noise_level', 
		   [ 'specific_zoom', 'zoom' ], 1 ],
		 'results-zoom-rmsnoiselevel-poorweather':
		 [ 'sensitivities', 'rms_noise_level',
		   [ 'specific_zoom', 'zoom' ], 2 ],
		 'results-zoom-brightnesstemperature-goodweather':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   [ 'specific_zoom', 'zoom' ], 0 ],
		 'results-zoom-brightnesstemperature-averageweather':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   [ 'specific_zoom', 'zoom' ], 1 ],
		 'results-zoom-brightnesstemperature-poorweather':
		 [ 'sensitivities', 'brightness_temperature_sensitivity',
		   [ 'specific_zoom', 'zoom' ], 2 ]

	     };
	     var gotResults = function(data) {
		 // console.log(data);
		 // Populate the results pages.
		 for (var rId in resultsIds) {
		     if (resultsIds.hasOwnProperty(rId)) {
			 var t = data;
			 var tu = '';
			 for (var i = 0; i < resultsIds[rId].length; i++) {
			     if (resultsIds[rId][i] instanceof Array) {
				 for (var j = 0; j < resultsIds[rId][i].length; j++) {
				     if (typeof t[resultsIds[rId][i][j]] !== 'undefined' &&
					 t[resultsIds[rId][i][j]] !== 0) {
					 t = t[resultsIds[rId][i][j]];
					 break;
				     }
				 }
			     } else {
				 t = t[resultsIds[rId][i]];
			     }
			     if (!atnf.isNumeric(resultsIds[rId][i])) {
				 if (resultsIds[rId][i] instanceof Array) {
				     for (var j = 0; j < resultsIds[rId][i].length; j++) {
					 if (typeof data['units'][resultsIds[rId][i][j]] !== 
					     'undefined') {
					     tu = data['units'][resultsIds[rId][i][j]];
					     break;
					 }
				     }
				 } else if (typeof data['units'][resultsIds[rId][i]] !== 
					    'undefined') {
				     tu = data['units'][resultsIds[rId][i]];
				 }
			     }
			 }
			 // console.log(rId + ' = ' + t);
			 
			 if (t instanceof Array) {
			     t = t.join(' x ');
			 }
			 domAttr.set(rId, 'innerHTML', t + ' ' + tu);
			 domClass.add(rId, 'filled-result');
		     }
		 }

		 // Replace the image source.
		 if (typeof data['output_plot'] !== 'undefined') {
		     dom.byId('results-spectral-rms-image').src =
			 data['output_plot'];
		     dom.byId('modal-spectral-rms-image').src =
			 data['output_plot'];
		 }

		 // Determine which results page to show.
		 query('.results-summary', dom.byId('panel-results-summary')).
		     addClass('invisible');
		 if (query('[name="data-required"]:checked').val() === 'Integration') {
		     if (domAttr.get('data-cabb-zoomfreq', 'value') !== '') {
			 // Display the zoom summary, for RMS sensitivity.
			 domClass.remove('results-summary-zoom-integration', 'invisible');
		     } else {
			 if (domAttr.get('data-rest-frequency', 'value') !== '') {
			     // Display the spectral line summary, for RMS sensitivity.
			     domClass.remove('results-summary-spectral-integration', 'invisible');
			 } else {
			     // Display the continuum summary, for RMS sensitivity.
			     domClass.remove('results-summary-continuum-integration', 'invisible');
			 }
		     }
		 } else if (query('[name="data-required"]:checked').val() === 'Sensitivity') {
		     var weatherVal = query('[name="data-sensitivity-weather"]:checked').val();
		     domAttr.set('results-summary-continuum-sensitivity-weather', 'innerHTML',
				 weatherVal);
		     domClass.add('results-summary-continuum-sensitivity-weather', 'filled-result');
		     domAttr.set('results-summary-spectral-sensitivity-weather', 'innerHTML',
				 weatherVal);
		     domClass.add('results-summary-spectral-sensitivity-weather', 'filled-result');
		     domAttr.set('results-summary-zoom-sensitivity-weather', 'innerHTML',
				 weatherVal);
		     domClass.add('results-summary-zoom-sensitivity-weather', 'filled-result');
		     var bandVal = query('[name="data-sensitivity-mode"]:checked').val();
		     if (bandVal === 'continuum') {
			 domClass.remove('results-summary-continuum-sensitivity', 'invisible');
		     } else if (bandVal === 'spectrum') {
			 domClass.remove('results-summary-spectral-sensitivity', 'invisible');
		     } else if (bandVal === 'zoom') {
			 domClass.remove('results-summary-zoom-sensitivity', 'invisible');
		     }
		 }

		 // Decide which resolution to show.
		 if (dom.byId('data-include-ca06').checked) {
		     domClass.add('results-continuum-synthesisedbeam', 'invisible');
		     domClass.remove('results-continuum-synthesisedbeambest', 'invisible');
		 } else {
		     domClass.remove('results-continuum-synthesisedbeam', 'invisible');
		     domClass.add('results-continuum-synthesisedbeambest', 'invisible');
		 }

		 // Show the results panel.
		 interviewSwitchPanel('panel-results-summary');

	     };

	     // The routine to query the server for the calculation.
	     var serverComms = function(pack) {
		 return xhr('/cgi-bin/obstools/atsen_general.pl', {
		     'data': pack,
		     'handleAs': 'json',
		     'method': 'POST'
		 });
	     };

	     // Do some checks and then do the calculation.
	     var beginCalculation = function() {
		 var pack = {};
		 pack['configuration'] = query('[name="data-array"]:checked').val();
		 pack['frequency'] = domAttr.get('data-cabb-centralfreq', 'value');
		 if (pack['frequency'] === '' ||
		     !bandName(parseInt(pack['frequency']))) {
		     showAlert('modal-error-cabbfreq');
		     return;
		 }
		 if (!errorChecks('data-declination') ||
		     !errorChecks('data-elevation-limit') ||
		     !errorChecks('data-hourangle-limit')) {
		     return;
		 }
		 pack['dec'] = domAttr.get('data-declination', 'value');
		 pack['ellimit'] = domAttr.get('data-elevation-limit', 'value');
		 pack['halimit'] = domAttr.get('data-hourangle-limit', 'value');
		 pack['bandwidth'] = query('[name="data-cabb-mode"]:checked').val();
		 pack['weight'] = query('[name="data-image-weight"]:checked').val();
		 var tmpVal = domAttr.get('data-cabb-zoomfreq', 'value');
		 if (tmpVal !== '') {
		     if (!bandName(parseInt(tmpVal))) {
			 showAlert('modal-error-zoomfreq');
			 return;
		     }
		     pack['s_zoom'] = tmpVal;
		 }
		 var opMode = query('[name="data-required"]:checked').val();
		 if (opMode === 'Integration') {
		     pack['integration'] = domAttr.get('data-integration', 'value');
		 } else if (opMode === 'Sensitivity') {
		     pack['target'] = domAttr.get('data-sensitivity', 'value');
		     pack['target-band'] = 
			 query('[name="data-sensitivity-mode"]:checked').val();
		     if (pack['target-band'] === 'zoom' && pack['s_zoom']) {
			 pack['target-band'] = 'specific';
		     }
		     pack['target-weather'] = 
			 query('[name="data-sensitivity-weather"]:checked').val();
		     tmpVal = query('[name="data-sensitivity-units"]:checked').val();
		     if (tmpVal === 'K') {
			 pack['target-kelvin'] = true;
		     }
		 }
		 pack['useca06'] = (dom.byId('data-include-ca06').checked) ?
		     'yes' : 'no';
		 pack['boxcar'] = domAttr.get('data-smoothing', 'value');
		 pack['zooms'] = domAttr.get('data-nzooms', 'value');
		 tmpVal = domAttr.get('data-rest-frequency', 'value');
		 if (tmpVal !== '') {
		     if (/\=/.test(tmpVal)) {
			 tmpArr = /^.*\=\s+(.*)$/.exec(tmpVal);
			 tmpVal = tmpArr[1];
		     }
		     pack['restfrequency'] = tmpVal;
		 }
		 pack['selfgen'] = (dom.byId('data-remove-birdies').checked) ?
		     1 : 0;
		 pack['rfi'] = (dom.byId('data-remove-rfi').checked) ? 1 : 0;
		 tmpVal = domAttr.get('data-remove-edge', 'value');
		 if (tmpVal > 0) {
		     pack['edge'] = tmpVal;
		 }
		 serverComms(pack).then(gotResults);
	     };
	     on(dom.byId('data-calculate'), 'click', beginCalculation);
	     on(dom.byId('interactive-calculate'), 'click', beginCalculation);

	     // A routine to reset all the parameters to their defaults.
	     var resetDefaults = function(e) {
		 for (var i = 0; i < linkedElements.length; i++) {
		     for (var j = 0; j < linkedElements[i].length; j++) {
			 var domEl = dom.byId(linkedElements[i][j]);
			 if (domEl) {
			     if (domEl.type === 'checkbox') {
				 domEl.checked = elementDefaults[i];
			     } else {
				 domAttr.set(domEl, 'value', elementDefaults[i]);
			     }
			 } else {
			     query('[name="' + linkedElements[i][j] + '"]').
				 val(elementDefaults[i]);
			 }
		     }
		 }
		 domAttr.set('data-rest-frequency', 'value', '');
		 domAttr.set('interactive-line-frequency', 'value', '');
	     };
	     on(dom.byId('data-reset'), 'click', resetDefaults);

	     on(dom.byId('results-summary-chooser-continuum'), 'click', function(e) {
		 query('.results-summary', dom.byId('panel-results-summary')).
		     addClass('invisible');
		 if (query('[name="data-required"]:checked').val() === 'Integration') {
		     domClass.remove('results-summary-continuum-integration', 'invisible');
		 } else {
		     domClass.remove('results-summary-continuum-sensitivity', 'invisible');
		 }
	     });
	     on(dom.byId('results-summary-chooser-spectral'), 'click', function(e) {
		 query('.results-summary', dom.byId('panel-results-summary')).
		     addClass('invisible');
		 if (query('[name="data-required"]:checked').val() === 'Integration') {
		     domClass.remove('results-summary-spectral-integration', 'invisible');
		 } else {
		     domClass.remove('results-summary-spectral-sensitivity', 'invisible');
		 }
	     });
	     on(dom.byId('results-summary-chooser-zoom'), 'click', function(e) {
		 query('.results-summary', dom.byId('panel-results-summary')).
		     addClass('invisible');
		 if (query('[name="data-required"]:checked').val() === 'Integration') {
		     domClass.remove('results-summary-zoom-integration', 'invisible');
		 } else {
		     domClass.remove('results-summary-zoom-sensitivity', 'invisible');
		 }
	     });

	     query('.results-interview-restart').on('click', function(e) {
		 interviewSwitchPanel(interviewDeterminePanel(null, null));
	     });
	     query('.results-interview-reset-restart').on('click', function(e) {
		 resetDefaults(e);
		 interviewSwitchPanel(interviewDeterminePanel(null, null));
	     });
	     query('.results-summary-panel').on('click', function(e) {
		 interviewSwitchPanel('panel-results-summary');
	     });
	     query('.results-array-panel').on('click', function(e) {
		 interviewSwitchPanel('panel-results-array');
	     });
	     query('.results-continuum-panel').on('click', function(e) {
		 interviewSwitchPanel('panel-results-continuum');
	     });
	     query('.results-spectrum-panel').on('click', function(e) {
		 interviewSwitchPanel('panel-results-spectrum');
	     });
	     query('.results-zoom-panel').on('click', function(e) {
		 interviewSwitchPanel('panel-results-zoom');
	     });
	     on(dom.byId('results-spectral-rms-image'), 'click', function(e) {
		 showAlert('modal-rms-image');
	     });
	     
		 
	 });
