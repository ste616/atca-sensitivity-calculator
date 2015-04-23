dojo.require('dojo.fx');
dojo.require('dojox.NodeList.delegate');
dojo.require('dojox.image.Lightbox');
dojo.require('dojo.hash');
dojo.require('dojo.cookie');
dojo.require('dijit.Tooltip');
dojo.require('dijit.TooltipDialog');

var init = function() {
    // Information about the bands the ATCA has.
    var bands = {
	'16cm': { lowCentre: 1730, highCentre: 2999,
		  recommended: [ 2100 ] },
	'6cm':  { lowCentre: 4928, highCentre: 7200,
		  recommended: [ 5500 ] },
	'3cm':  { lowCentre: 7201, highCentre: 10928,
		  recommended: [ 9000 ] },
	'15mm': { lowCentre: 16000, highCentre: 25000,
		  recommended: [ 17000, 19000 ] },
	'7mm':  { lowCentre: 30000, highCentre: 50000,
		  recommended: [ 33000, 35000, 43000, 45000 ] },
	'3mm':  { lowCentre: 83857, highCentre: 104785,
		  recommended: [ 93000, 95000 ] },
    };

    var continuumLightbox = null;

    // This routine is called to set the continuum central frequency
    // via a mouse click on a recommended frequency.
    var insertRecommended = function(evtObj) {
	dojo.attr('frequency_selection', 'value',
		  dojo.attr(evtObj.target, 'innerHTML'));
    };

    // Add the indicator elements to the table.
    dojo.query('tr', 'parameters_table').forEach(function(node, index, nodeList) {
	    var a = dojo.create('td', {
		    'class': 'indicatorCorrect'
		});
	    node.appendChild(a);
	    var s = dojo.create('img', {
		    src: 'tick-circle.png',
		    class: 'fieldOk hidden'
		});
	    var n = dojo.create('img', {
		    src: 'cross-circle.png',
		    class: 'fieldBad hidden'
		});
	    a.appendChild(s);
	    a.appendChild(n);
	    a = dojo.create('td', {
		    'class': 'indicatorInfo'
		});
	    node.appendChild(a);
	    var i = dojo.create('img', {
		    src: 'information.png',
		    class: 'fieldInfo hidden'
		});
	    a.appendChild(i);
	});

    var checkAllParams = function() {
	for (var i = 0; i < selectionIds.length; i++) {
	    checkParam(selectionIds[i]);
	}
    };

    var checkParam = function(name) {
	// Check only the ID given in name.
	var v = dojo.attr(name, 'value');
	var ok = false;
	var na = false;
	var index = -1;
	var errorMessage = '';
	switch (name) {
	case 'frequency_selection':
	    for (var band in bands) {
		if (bands.hasOwnProperty(band)) {
		    if (v >= bands[band].lowCentre &&
			v <= bands[band].highCentre) {
			ok = true;
		    }
		}
	    }
	    if (ok === false) {
		errorMessage = 'This centre frequency is not supported at ATCA.';
	    }
	    break;
	case 'zoom_frequency_selection':
	    if (v === '') {
		na = true;
	    } else {
		var c = dojo.attr('frequency_selection', 'value');
		if (v >= (c - 1024) &&
		    v <= (c + 1024)) {
		    ok = true;
		} else {
		    var cFreq = -1;
		    for (var band in bands) {
			if (bands.hasOwnProperty(band)) {
			    if (v >= (bands[band].lowCentre - 1024) &&
				v <= (bands[band].highCentre + 1024)) {
				cFreq = v;
				for (var i = 0; i < bands[band].recommended.length; i++) {
				    if (v >= (bands[band].recommended[i] - 1024) &&
					v <= (bands[band].recommended[i] + 1024)) {
					cFreq = bands[band].recommended[i];
				    }
				}
			    }
			}
		    }
		    if (cFreq > 0) {
			dojo.attr('frequency_selection', 'value', cFreq);
			entryChanged({
				target: dojo.byId('frequency_selection')
				    });
		    } else {
			errorMessage = 'This frequency is not supported at ATCA.';
		    }
		}
	    }
	    break;
	case 'baseline_selection':
	    if (v !== '') {
		ok = true;
	    } else {
		errorMessage = 'Select a configuration.';
	    }
	    break;
	case 'antenna6_selection':
	    ok = true;
	    break;
	case 'fourcm_selection':
	    if (v >= 0 && v <= 6) {
		ok = true;
	    } else {
		errorMessage = 'You cannot have more than six receivers, or fewer than none.';
	    }
	    break;
	case 'cabb_selection':
	    if (v !== '') {
		ok = true;
	    } else {
		errorMessage = 'Select a CABB configuration.';
	    }
	    break;
	case 'concatenation_selection':
	    if (v >= 1 && v <= 16) {
		ok = true;
	    } else {
		errorMessage = 'You cannot concatenate more than sixteen zoom channels, ' +
		    'or fewer than 1.';
	    }
	    break;
	case 'declination_selection':
	    if (v >= -90 && v <= 48) {
		ok = true;
	    } else {
		errorMessage = 'The ATCA can observe sources between declinations of -90 degrees ' +
		    'and +48 degrees.';
	    }
	    break;
	case 'integration_selection':
	    if (v > 0) {
		ok = true;
	    } else {
		errorMessage = 'You must specify a positive, non-zero integration time.';
	    }
	    break;
	case 'elevation_selection':
	    if (v >= 12 && v <= 90) {
		ok = true;
	    } else {
		errorMessage = 'The elevation limit of the ATCA is 12 degrees.';
	    }
	    break;
	case 'hourangle_selection':
	    if (v > 0 && v < 12) {
		ok = true;
	    } else {
		errorMessage = 'The hour-angle should be specified between 0 and 12 hours.';
	    }
	    break;
	case 'weighting_selection':
	    ok = true;
	    break;
	case 'boxcar_selection':
	    if (v >= 1) {
		ok = true;
	    } else {
		errorMessage = 'The filter width must be a positive integer.';
	    }
	    break;
	case 'restfreq_selection':
	    if (v === '') {
		na = true;
	    } else if (v > 0) {
		ok = true;
	    } else {
		errorMessage = 'The rest frequency must be a positive number.';
	    }
	    break;
	case 'selfgen_selection':
	    ok = true;
	    break;
	case 'rfi_selection':
	    ok = true;
	    break;
	case 'edge_selection':
	    if (v === '') {
		na = true;
	    } else if (v >= 0) {
		ok = true;
	    } else {
		errorMessage = 'The number of edge channels must be specified ' +
		    'as a positive integer.';
	    }
	    break;
	}

	for (var i = 0; i < selectionIds.length; i++) {
	    if (name === selectionIds[i]) {
		selectionOk[i] = ok || na;
		index = i;
	    }
	}
	
	var iNode = dojo.query('~ td.indicatorCorrect', dojo.byId(name).parentNode);
	if (na === true) {
	    dojo.query('> .fieldOk', iNode[0]).addClass('hidden');
	    dojo.query('> .fieldBad', iNode[0]).addClass('hidden');
	} else if (ok === true) {
	    dojo.query('> .fieldOk', iNode[0]).removeClass('hidden');
	    dojo.query('> .fieldBad', iNode[0]).addClass('hidden');
	} else {
	    dojo.query('> .fieldOk', iNode[0]).addClass('hidden');
	    var badField = dojo.query('> .fieldBad', iNode[0]);
	    badField.removeClass('hidden');
	    if (index >=0) {
		if (selectionErrorTip[index] === null) {
		    selectionErrorTip[index] = new dijit.Tooltip({
			    connectId: badField,
			    label: errorMessage
			});
		} else {
		    selectionErrorTip[index].set('label', errorMessage);
		}
	    }
	}
    };

    var entryChanged = function(evtObj) {
	// This routine gets called whenever an entry box is changed.
	
	// Get the hash.
	var hashValue = dojo.queryToObject(dojo.hash());
	// Get the new value of the changed box.
	var entryValue = dojo.attr(evtObj.target, 'value');
	hashValue[evtObj.target.id] = entryValue;
	// Set the hash again.
	dojo.hash(dojo.objectToQuery(hashValue));

	checkParam(evtObj.target.id);
    };

    var selectionIds = [ 'frequency_selection', 'zoom_frequency_selection',
			 'baseline_selection', 'antenna6_selection',
			 'fourcm_selection', 'cabb_selection',
			 'concatenation_selection', 'declination_selection',
			 'integration_selection', 'elevation_selection',
			 'hourangle_selection', 'weighting_selection',
			 'boxcar_selection', 'restfreq_selection',
			 'selfgen_selection', 'rfi_selection',
			 'edge_selection' ];
    var selectionDefaults = [ '', '',
			      '', 'yes',
			      '6', '',
			      '1', '-30',
			      '720', '12',
			      '6', 'N',
			      '1', '',
			      'no', 'no',
			      '0' ];
    var selectionOk = [];
    var selectionErrorTip = [];

    var hashToSettings = function() {
	var hashValue = dojo.queryToObject(dojo.hash());
	
	for (var j = 0; j < selectionIds.length; j++) {
	    if (typeof hashValue[selectionIds[j]] !== 'undefined') {
		dojo.attr(selectionIds[j], 'value', hashValue[selectionIds[j]]);
	    } else {
		dojo.attr(selectionIds[j], 'value', selectionDefaults[j]);
	    }
	}
	checkAllParams();
    };
    
    for (var i = 0; i < selectionIds.length; i++) {
	// Check for a cookie value to override the default.
	var cEntry = dojo.cookie(selectionIds[i]);
	if (cEntry) {
	    selectionDefaults[i] = cEntry;
	}
	selectionErrorTip[i] = null;
    }

    hashToSettings();
    checkAllParams();
    dojo.subscribe('/dojo/hashchange', hashToSettings);

    for (var i = 0; i < selectionIds.length; i++) {
	// Watch for changes.
	if (dojo.byId(selectionIds[i]) === null) {
	    console.log('cannot find id = ' + selectionIds[i]);
	    continue;
	}
	dojo.connect(dojo.byId(selectionIds[i]), 'onchange', entryChanged);
    }

    var saveDefaults = function() {
	for (var i = 0; i < selectionIds.length; i++) {
	    if (selectionOk[i] === true) {
		dojo.cookie(selectionIds[i], dojo.attr(selectionIds[i], 'value'), {
			expires: 999
		    });
	    }
	}
    };
    
    var resultsReceived = function(data, ioargs) {
	dojo.removeClass('results_of_calculation', 'hidden');
	// Check for the presence of specific zoom mode data.
	var specZoom = false;
	if (typeof data.specific_zoom !== 'undefined') {
	    specZoom = true;
	    dojo.removeClass('specific_zoom_region', 'hidden');
	}
	var bits = ['parameters', 'source_imaging', 'continuum', 'zoom'];
	if (specZoom === true) {
	    bits.push('specific_zoom');
	}
	for (var r = 0; r < bits.length; r++) {
	    for (var point in data[bits[r]]) {
		var insertion = '';
		var checkId = 'results_' + bits[r] + '_' + point;
		if (dojo.byId(checkId) !== null) {
		    if (data[bits[r]][point] instanceof Array) {
		        for (var a = 0; a < data[bits[r]][point].length; a++) {
			    if (a > 0) {
				insertion += ' x ';
			    }
			    insertion += data[bits[r]][point][a];
			}
		    } else {
			insertion = data[bits[r]][point];
		    }
		    if (typeof data.units[point] !== 'undefined') {
			insertion += ' ' + data.units[point];
		    }
		    dojo.attr(checkId, 'innerHTML', insertion);
		}
	    }
	}
	// Make some results tables.
	var makeResultsTable = function(spanId, params, option) {
	    // var arrayTableParent = dojo.byId('resultstable_sensitivities_array');
	    var arrayTableParent = dojo.byId(spanId);
	    if (arrayTableParent !== null) {
		dojo.empty(arrayTableParent);
		var table = dojo.create('table', {
			'class': 'resultsTable'
		    }, arrayTableParent);
		var header = dojo.create('thead');
		table.appendChild(header);
		var weatherRow = dojo.create('tr');
		header.appendChild(weatherRow);
		dojo.place('<td></td>', weatherRow);
		var nWeathers = data.description.sensitivities.length;
		for (var c = 0; c < nWeathers; c++) {
		    var w = dojo.create('td', {
			    'innerHTML': data.description.sensitivities[c]
			});
		    weatherRow.appendChild(w);
		}
		// var params = ['system_temperature', 'antenna_sensitivity',
		//			      'array_sensitivity'];
		for (var p = 0; p < params.length; p++) {
		    var paramRow = dojo.create('tr');
		    table.appendChild(paramRow);
		    var title = dojo.create('th', {
			    'innerHTML': data.description[params[p]]
			});
		    paramRow.appendChild(title);
		    for (var c = 0; c < nWeathers; c++) {
			var entry;
			if (data.sensitivities[params[p]] instanceof Array) {
			    entry = data.sensitivities[params[p]][c];
			} else {
			    entry = data.sensitivities[params[p]][option][c];
			}
			if (typeof data.units[params[p]] !== 'undefined') {
			    entry += ' ' + data.units[params[p]];
			}
			var v = dojo.create('td', {
				'innerHTML': entry
			    });
			paramRow.appendChild(v);
		    }
		}
	    }
	}
	makeResultsTable('resultstable_sensitivities_array',
			 ['system_temperature', 'antenna_sensitivity',
			  'array_sensitivity']);
	makeResultsTable('resultstable_sensitivities_continuum',
			 ['rms_noise_level', 'brightness_temperature_sensitivity'],
			 'continuum');
	makeResultsTable('resultstable_sensitivities_spectral',
			 ['rms_noise_level', 'brightness_temperature_sensitivity'],
			 'spectral');
	makeResultsTable('resultstable_sensitivities_zoom',
			 ['rms_noise_level', 'brightness_temperature_sensitivity'],
			 'zoom');
	if (specZoom === true) {
	    makeResultsTable('resultstable_sensitivities_specific_zoom_array',
			     ['specific_zoom_system_temperature']);
	    makeResultsTable('resultstable_sensitivities_specific_zoom',
			     ['rms_noise_level', 'brightness_temperature_sensitivity'],
			     'specific_zoom');
	}

	// Make an image lightbox.
	continuumLightbox = new dojox.image.Lightbox({
		title: 'Continuum RMS noise map',
		group: 'rmsImages',
		href: '../' + data.output_plot
	    });
	continuumLightbox.startup();
	dojo.attr('continuum_rms_image', 'src', '../' + data.output_plot);
	dojo.connect(dojo.byId('continuum_rms_image'), 'onclick',
		     function(evtObj) {
			 continuumLightbox.show();
		     });
    };

    var resultsError = function(error, ioargs) {
	console.log(error);
    };

    var calculate = function(evtObj) {
	dojo.stopEvent(evtObj);
	var params = {};
	if (continuumLightbox !== null) {
	    continuumLightbox.destroy();
	    continuumLightbox = null;
	}
	params.configuration = dojo.attr('baseline_selection', 'value');
	params.frequency = dojo.attr('frequency_selection', 'value');
	params.dec = dojo.attr('declination_selection', 'value');
	params.ellimit = dojo.attr('elevation_selection', 'value');
	params.halimit = dojo.attr('hourangle_selection', 'value');
	params.bandwidth = dojo.attr('cabb_selection', 'value');
	params.weight = dojo.attr('weighting_selection', 'value');
	params.integration = dojo.attr('integration_selection', 'value');
	params.useca06 = dojo.attr('antenna6_selection', 'value');
	params.boxcar = dojo.attr('boxcar_selection', 'value');
	params.zooms = dojo.attr('concatenation_selection', 'value');
	if (dojo.attr('zoom_frequency_selection', 'value') !== '') {
	    params.s_zoom = dojo.attr('zoom_frequency_selection', 'value');
	}
	if (dojo.attr('restfreq_selection', 'value') !== '') {
	    params.restfrequency = dojo.attr('restfreq_selection', 'value');
	}
	params.fourcm = dojo.attr('fourcm_selection', 'value');
	if (dojo.attr('selfgen_selection', 'value') === 'yes') {
	    params.selfgen = 1;
	}
	if (dojo.attr('rfi_selection', 'value') === 'yes') {
	    params.rfi = 1;
	}
	if (dojo.attr('edge_selection', 'value') > 0) {
	    params.edge = dojo.attr('edge_selection', 'value');
	}

	var calcPromise = dojo.xhrPost({
		url: '/cgi-bin/obstools/atsen_general.pl',
		sync: false,
		content: params,
		handleAs: 'json',
		load: resultsReceived,
		error: resultsError
	    });
    }

    dojo.connect(dojo.byId('calcsens_table_button'), 'onclick', calculate);
    dojo.connect(dojo.byId('reset_defaults_button'), 'onclick', function(evtObj) {
	    dojo.hash('');
	});
    dojo.connect(dojo.byId('restfreq_setter'), 'onclick', function(evtObj) {
	    dojo.attr('restfreq_selection', 'value',
		      dojo.attr('restfreq_chooser', 'value'));
	    entryChanged({
		    target: dojo.byId('restfreq_selection')
			});
	});
    dojo.connect(dojo.byId('save_defaults_button'), 'onclick', saveDefaults);
};

dojo.addOnLoad(init);
