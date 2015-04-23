dojo.require('dojo.fx');
dojo.require('dojox.NodeList.delegate');
dojo.require('dojox.image.Lightbox');

var atnfAccordion = function(spec, my) {
    var that = {};

    spec = spec || {};

    spec.toggleClass = spec.toggleClass || 'accordion_toggle';
    spec.contentClass = spec.contentClass || 'accordion_content';
    if (typeof spec.multiOpen === 'undefined') {
	spec.multiOpen = true;
    }

    var togglers = [];
    
    // Initialise the accordion.
    var initialise = function() {
	// Get a list of all the toggle areas.
	var toggleAreas = dojo.query('.' + spec.toggleClass);
	toggleAreas.delegate('*', 'onclick', clickDummy);
								      
	// Get a list of all the content areas.
	var contentAreas = dojo.query('.' + spec.contentClass);
	for (var j = 0; j < toggleAreas.length; j++) {
	    togglers.push({
		    'toggler': toggleAreas[j],
			'index': j,
			'content': contentAreas[j],
			'open': true,
			'handler': new dojo.fx.Toggler({
				node: contentAreas[j],
				    showFunc: dojo.fx.wipeIn,
				    hideFunc: dojo.fx.wipeOut
				    })
			});
	    dojo.connect(toggleAreas[j], 'onclick', togglers[j], clickHandler);
	    if (spec.multiOpen === false && j > 0) {
		// Close all but the first one.
		accordionClose(j);
	    }
	}

    };

    var clickDummy = function(evtObj) {
	if (typeof this.open !== 'undefined') {
	    dojo.stopEvent(evtObj);
	}
	return;
    }
    
    var clickHandler = function(evtObj) {
	// Which handler triggered us?
	if (typeof this.index === 'undefined') {
	    return;
	}
	// Stop this event from going further.
	dojo.stopEvent(evtObj);
	if (togglers[this.index].open === true) {
	    accordionClose(this.index);
	} else {
	    accordionOpen(this.index);
	}
    };

    // Find the specified ID among the togglers.
    var findId = function(fId) {
	for (var i = 0; i < togglers.length; i++) {
	    if (dojo.attr(togglers[i].toggler, 'id') === fId) {
		return i;
	    }
	}
	return -1;
    };

    // Open the specified accordion.
    var accordionOpen = function(tIndex) {
	if (togglers[tIndex].open === true) {
	    return;
	}
	togglers[tIndex].handler.show();
	togglers[tIndex].open = true;
	if (spec.multiOpen === false) {
	    // Close any other open panels.
	    for (var k = 0; k < togglers.length; k++) {
		if (k !== tIndex && togglers[k].open === true) {
		    accordionClose(k);
		}
	    }
	}
    };

    var accordionClose = function(tIndex) {
	if (togglers[tIndex].open === false) {
	    return;
	}
	togglers[tIndex].handler.hide();
	togglers[tIndex].open = false;
    };

    var findIndex = function(identifier) {
	var index = -1;
	// Check for an ID with that identifier.
	index = findId(identifier);
	if (index === -1) {
	    // No ID, perhaps the element number.
	    if ((parseFloat(identifier) == parseInt(identifier)) &&
		!isNaN(identifier) && 
		parseInt(identifier) < togglers.length) {
		index = parseInt(identifier);
	    }
	}
	return index;
    }

    that.open = function(identifier) {
	var index = findIndex(identifier);
	if (index === -1) {
	    return;
	}
	accordionOpen(index);
    }

    that.close = function(identifier) {
	var index = findIndex(identifier);
	if (index === -1) {
	    return;
	}
	accordionClose(index);
    }

    that.status = function() {
	for (var t = 0; t < togglers.length; t++) {
	    console.log(togglers[t].index + ': ' + togglers[t].open);
	}
    }

    initialise();

    return that;
    
};

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
	'selected': null
    };

    var continuumLightbox = null;

    var PsNoFrequency = 1;
    var PsFrequencySelected = 2;
    var PsArraySelected = 3;
    var PsCorrelatorSelected = 4;
    var PsCalculationReady = 5;
    var PsCalculationDone = 6;
    var progressState = PsNoFrequency;

    // Set up the accordion.
    var sensAccordion = atnfAccordion();

    var manageProgress = function(finished) {
	// Determine the progress.
	if (dojo.attr('observing_frequency_setting', 'innerHTML') === 'Not set') {
	    progressState = PsNoFrequency;
	} else if (dojo.attr('array_configuration_setting', 'innerHTML') === 'Not set') {
	    progressState = PsFrequencySelected;
	} else if (dojo.attr('correlator_configuration_setting', 'innerHTML') === 'Not set') {
	    progressState = PsArraySelected;
	} else if (dojo.attr('observation_setting', 'innerHTML') === 'Not set') {
	    progressState = PsCorrelatorSelected;
	} else if (finished !== true) {
	    progressState = PsCalculationReady;
	} else {
	    progressState = PsCalculationDone;
	}

	if (progressState === PsNoFrequency) {
	    sensAccordion.close('array_toggle');
	    sensAccordion.close('correlator_toggle');
	    sensAccordion.close('observation_toggle');
	    sensAccordion.close('reduction_toggle');
	    sensAccordion.close('results_toggle');
	} else if (progressState === PsFrequencySelected) {
	    sensAccordion.open('array_toggle');
	    sensAccordion.close('correlator_toggle');
	    sensAccordion.close('observation_toggle');
	    sensAccordion.close('reduction_toggle');
	    sensAccordion.close('results_toggle');
	} else if (progressState === PsArraySelected) {
	    sensAccordion.open('correlator_toggle');
	    sensAccordion.close('observation_toggle');
	    sensAccordion.close('reduction_toggle');
	    sensAccordion.close('results_toggle');
	} else if (progressState === PsCorrelatorSelected) {
	    sensAccordion.open('observation_toggle');
	    sensAccordion.open('reduction_toggle');
	    sensAccordion.close('results_toggle');
	    if (dojo.attr('observation_setting', 'innerHTML') !== 'Not set' &&
		dojo.attr('reduction_setting', 'innerHTML') !== 'Not set') {
		progressState = PsCalculationReady;
	    }
	}
	
	if (progressState === PsCalculationReady) {
	    dojo.addClass('results_notready', 'hidden');
	    dojo.addClass('results_available', 'hidden');
	    dojo.removeClass('results_ready', 'hidden');
	    sensAccordion.open('observation_toggle');
	    sensAccordion.open('reduction_toggle');
	    sensAccordion.close('results_toggle');
	} else if (progressState === PsCalculationDone) {
	    dojo.addClass('results_notready', 'hidden');
	    dojo.removeClass('results_available', 'hidden');
	    dojo.addClass('results_ready', 'hidden');
	    sensAccordion.open('results_toggle');
	    sensAccordion.close('array_toggle');
	    sensAccordion.close('correlator_toggle');
	    sensAccordion.close('observation_toggle');
	    sensAccordion.close('reduction_toggle');
	    sensAccordion.close(0);
	} else {
	    dojo.removeClass('results_notready', 'hidden');
	    dojo.addClass('results_available', 'hidden');
	    dojo.addClass('results_ready', 'hidden');
	    sensAccordion.close('results_toggle');
	}
    };

    // This routine is called to set the continuum central frequency
    // via a mouse click on a recommended frequency.
    var insertRecommended = function(evtObj) {
	dojo.attr('frequency_selection', 'value',
		  dojo.attr(evtObj.target, 'innerHTML'));
	frequencyChanged();
    };

    // This routine is called when the user selects a band button.
    // It gives the user information about the allowed centre frequency
    // range, and the recommended continuum frequencies.
    var bandSelected = function(evtObj) {
	var bandArr;
	if (/button\_(.*)$/.test(evtObj.target.id)) {
	    bandArr = /button\_(.*)$/.exec(evtObj.target.id);
	} else {
	    bandArr = /bandtable\_(.*)$/.exec(evtObj.target.id);
	}
	var bandId = bandArr[1];
	dojo.attr('bandNameHere', 'innerHTML', bandId);
	dojo.attr('bandLowFreqHere', 'innerHTML', bands[bandId].lowCentre);
	dojo.attr('bandHighFreqHere', 'innerHTML', bands[bandId].highCentre);
	if (bands[bandId].recommended.length > 1) {
	    dojo.attr('bandRecommendedModifier', 'innerHTML', 'frequencies are');
	} else {
	    dojo.attr('bandRecommendedModifier', 'innerHTML', 'frequency is');
	}
	dojo.empty(dojo.byId('bandRecommendedHere'));
	for (var i = 0; i < bands[bandId].recommended.length; i++) {
	    var prior = '<span>';
	    if (i > 0 && i === (bands[bandId].recommended.length - 1)) {
		prior += ' and ';
	    } else if (i > 0) {
		prior += ', ';
	    }
	    dojo.place(prior + '</span>', 'bandRecommendedHere');
	    var temp = dojo.create('span', {
		    'class': 'recommendedFrequency',
		    innerHTML: '' + bands[bandId].recommended[i]
		});
	    dojo.place(temp, 'bandRecommendedHere');
	    dojo.connect(temp, 'onclick', insertRecommended);
	}
	dojo.attr('frequency_selection', 'value', bands[bandId].recommended[0]);
	// Show the hidden bits.
	dojo.removeClass('hiding_element', 'hidden');
	frequencyChanged();
    };

    // This routine is called when the user has selected or entered a 
    // frequency into the continuum centre frequency box. This checks the
    // value is valid, and sets the error and title boxes appropriately.
    var frequencyChanged = function() {
	var isValid = false;
	var validBand = '';
	var freq = parseInt(dojo.attr('frequency_selection', 'value'));
	for (var band in bands) {
	    if (bands.hasOwnProperty(band)) {
		if (freq >= bands[band].lowCentre &&
		    freq <= bands[band].highCentre) {
		    isValid = true;
		    validBand = band;
		    bands.selected = band;
		}
	    }
	}
	if (isValid === false) {
	    dojo.attr('continuum_frequency_errors', 'innerHTML',
		      'This is not a supported CABB centre frequency.');
	    dojo.attr('observing_frequency_setting', 'innerHTML', 'Not set');
	    bands.selected = '';
	} else {
	    dojo.attr('continuum_frequency_errors', 'innerHTML', '');
	}
	// Do special things depending on what band is selected.
	if (validBand === '6cm' || validBand === '3cm') {
	    // Show the 4cm receiver box.
	    dojo.removeClass('fourcm_stuff', 'hidden');
	} else {
	    // Hide the 4cm receiver box.
	    dojo.addClass('fourcm_stuff', 'hidden');
	}
	if (validBand === '3mm') {
	    // Disable CA06.
	    dojo.attr('antenna6_selection', 'value', 'no');
	    dojo.attr('antenna6_selection', 'disabled', true);
	    dojo.attr('antenna6_preamble', 'innerHTML',
		      'There is no 3mm receiver on CA06.');
	} else {
	    // Allow selection of CA06.
	    dojo.attr('antenna6_selection', 'disabled', false);
	    dojo.empty('antenna6_preamble');
	}
	frequencyConfigChanged();
	arrayConfigChanged();
    };

    var frequencyConfigChanged = function() {
	var freq = parseInt(dojo.attr('frequency_selection', 'value'));
	var settingString = 'Not set';
	if (bands.selected !== '' && 
	    dojo.attr('continuum_frequency_errors', 'innerHTML') === '') {
	    settingString = freq + ' MHz (' + bands.selected + ' band)';
	    var zFreq = parseInt(dojo.attr('zoom_frequency_selection', 'value'));
	    if (zFreq > 0 &&
		dojo.attr('zoom_frequency_errors', 'innerHTML') === '') {
		settingString += ', zoom = ' + zFreq + ' MHz';
	    }
	}
	dojo.attr('observing_frequency_setting', 'innerHTML', settingString);
	manageProgress();
    };

    var zoomFrequencyChanged = function() {
	var isValid = false;
	var cFreq = parseInt(dojo.attr('frequency_selection', 'value'));
	var zFreq = parseInt(dojo.attr('zoom_frequency_selection', 'value'));
	var czDiff = Math.abs(cFreq - zFreq);
	if (czDiff < 1024 && bands.selected !== '')  {
	    isValid = true;
	}
	if (isValid === false) {
	    dojo.attr('zoom_frequency_errors', 'innerHTML',
		      'This zoom frequency does not lie within the 1024 MHz ' +
		      'of the continuum central frequency.');
	} else {
	    dojo.attr('zoom_frequency_errors', 'innerHTML', '');
	}
	frequencyConfigChanged();
    };

    // This routine determines what should be displayed in the title
    // area of the Array Configuration accordion element.
    var arrayConfigChanged = function() {
	var configString = 'Not set';
	var baseSelect = dojo.byId('baseline_selection');
	var baseChosen = baseSelect.options[baseSelect.selectedIndex];
	if (dojo.attr(baseChosen, 'value') !== '') {
	    configString = dojo.attr(baseChosen, 'innerHTML');
	    configString += ' / CA06 ';
	    if (dojo.attr('antenna6_selection', 'value') === 'no') {
		configString += 'not ';
	    }
	    configString += 'included';
	    var nFourCm = parseInt(dojo.attr('fourcm_selection', 'value'));
	    if (bands.selected === '6cm' || bands.selected === '3cm') {
		configString += ' / ';
		if (nFourCm === 0) {
		    configString += 'no';
		} else {
		    configString += nFourCm;
		}
		configString += ' 4cm receiver';
		if (nFourCm !== 1) {
		    configString += 's';
		}
	    }
	}
	dojo.attr('array_configuration_setting', 'innerHTML', configString);
	manageProgress();
    };

    // This routine is called when the maximum baseline select box is changed.
    var baselineConfigChanged = function() {
	// Try to set the CA06 box appropriately.
	if (bands.selected !== '3mm') {
	    if (dojo.attr('baseline_selection', 'value') === '6km') {
		dojo.attr('antenna6_selection', 'value', 'yes');
	    } else if (dojo.attr('baseline_selection', 'value') !== '') {
		dojo.attr('antenna6_selection', 'value', 'no');
	    }
	}
	arrayConfigChanged();
    };

    var fourcmChanged = function() {
	// Check that there is a valid number of receivers.
	var nRequested = parseInt(dojo.attr('fourcm_selection', 'value'));
	if (nRequested > 6) {
	    dojo.attr('fourcm_selection', 'value', 6);
	}
	if (dojo.attr('fourcm_selection', 'value') === '') {
	    dojo.attr('fourcm_selection', 'value', 0);
	}
	if (/^[^0-6]$/.test(dojo.attr('fourcm_selection', 'value'))) {
	    dojo.attr('fourcm_selection', 'value', 0);
	}
	arrayConfigChanged();
    };

    var cabbChanged = function() {
	var cabbSelect = dojo.byId('cabb_selection');
	var cabbChosen = cabbSelect.options[cabbSelect.selectedIndex];
	var settingString = 'Not set';
	if (dojo.attr(cabbChosen, 'value') !== '') {
	    settingString = dojo.attr(cabbChosen, 'innerHTML');
	}
	var cabbConcat = dojo.attr('concatenation_selection', 'value');
	if (cabbConcat < 1) {
	    cabbConcat = 1;
	    dojo.attr('concatenation_selection', 'value', cabbConcat);
	} else if (cabbConcat > 16) {
	    cabbConcat = 16;
	    dojo.attr('concatenation_selection', 'value', cabbConcat);
	}
	settingString += ' / ' + cabbConcat + ' zoom channel';
	if (cabbConcat > 1) {
	    settingString += 's concatenated';
	}
	dojo.attr('correlator_configuration_setting', 'innerHTML', settingString);
	manageProgress();
    };

    var observationChanged = function() {
	// Check the declination.
	var decValue = parseFloat(dojo.attr('declination_selection', 'value'));
	var decValid = true;
	if (decValue < -90 ||
	    decValue > 48) {
	    dojo.attr('declination_errors', 'innerHTML',
		      'You cannot observe this declination at the ATCA.');
	    decValid = false;
	}
	var elValue = parseFloat(dojo.attr('elevation_selection', 'value'));
	var elValid = true;
	if (elValue < 12 || elValue > 90) {
	    dojo.attr('limits_errors', 'innerHTML',
		      'The elevation limit is invalid: the ATCA can observe ' +
		      'between 12 and 90 degrees elevation.');
	    elValid = false;
	}
	var haValue = parseFloat(dojo.attr('hourangle_selection', 'value'));
	var haValid = true;
	if (haValue < 0) {
	    haValue = Math.abs(haValue);
	    dojo.attr('hourangle_selection', 'value', haValue);
	}
	if (haValue > 12) {
	    dojo.attr('limits_errors', 'innerHTML',
		      'The hour-angle limit is invalid.');
	    haValid = false;
	}
	if (decValid && elValid && haValid) {
	    var obsSetting = decValue + ' deg Dec, ' +
	    dojo.attr('integration_selection', 'value') + 
	    ' mins on-source above ' + elValue + ' deg el / ' +
	    ' between HA = +- ' + haValue;
	    if (dojo.attr('restfreq_selection', 'value') !== '') {
		obsSetting += ', line frequency = ' +
		    dojo.attr('restfreq_selection', 'value') + ' GHz';
	    }

	    dojo.attr('observation_setting', 'innerHTML', obsSetting);
	    dojo.attr('declination_errors', 'innerHTML', '');
	    dojo.attr('limits_errors', 'innerHTML', '');
	} else {
	    dojo.attr('observation_setting', 'innerHTML', 'Not set');
	}
	manageProgress();
    };

    var reductionChanged = function() {
	if (dojo.attr('edge_selection', 'value') === '') {
	    dojo.attr('edge_selection', 'value', 0);
	}
	var weightSelect = dojo.byId('weighting_selection');
	var weightChosen = weightSelect.options[weightSelect.selectedIndex];
	var settingString = dojo.attr(weightChosen, 'innerHTML') +
	' weighting / ';
	if (dojo.attr('boxcar_selection', 'value') == 1) {
	    settingString += 'No smoothing';
	} else {
	    settingString += 'Smoothing window of ' +
	    dojo.attr('boxcar_selection', 'value');
	}
	if (dojo.byId('selfgen_selection').checked ||
	    dojo.byId('rfi_selection').checked ||
	    dojo.attr('edge_selection', 'value') > 0) {
	    settingString += ' / Some flagging';
	} else {
	    settingString += ' / No flagging';
	}
	dojo.attr('reduction_setting', 'innerHTML', settingString);
	manageProgress();
    };

    var restFrequencySet = function(evtObj) {
	dojo.attr('restfreq_selection', 'value',
		  dojo.attr('restfreq_chooser', 'value'));
	observationChanged();
    };

    // Set the band buttons to call the appropriate helper function.
    for (var band in bands) {
	if (bands.hasOwnProperty(band)) {
	    if (dojo.byId('button_' + band) !== null) {
		dojo.connect(dojo.byId('button_' + band), 'onclick', bandSelected);
	    }
	    if (dojo.byId('bandtable_' + band) !== null) {
		dojo.connect(dojo.byId('bandtable_' + band), 'onclick', bandSelected);
	    }
	}
    }

    // Call the frequency checker routine if the user has changed the
    // continuum centre frequency.
    dojo.connect(dojo.byId('frequency_selection'), 'onchange', frequencyChanged);
    // And the zoom frequency.
    dojo.connect(dojo.byId('zoom_frequency_selection'), 'onchange', zoomFrequencyChanged);

    dojo.connect(dojo.byId('baseline_selection'), 'onchange', baselineConfigChanged);
    dojo.connect(dojo.byId('antenna6_selection'), 'onchange', arrayConfigChanged);
    dojo.connect(dojo.byId('fourcm_selection'), 'onchange', fourcmChanged);
    dojo.connect(dojo.byId('cabb_selection'), 'onchange', cabbChanged);
    dojo.connect(dojo.byId('concatenation_selection'), 'onchange', cabbChanged);
    dojo.connect(dojo.byId('declination_selection'), 'onchange', observationChanged);
    dojo.connect(dojo.byId('integration_selection'), 'onchange', observationChanged);
    dojo.connect(dojo.byId('elevation_selection'), 'onchange', observationChanged);
    dojo.connect(dojo.byId('hourangle_selection'), 'onchange', observationChanged);
    dojo.connect(dojo.byId('weighting_selection'), 'onchange', reductionChanged);
    dojo.connect(dojo.byId('boxcar_selection'), 'onchange', reductionChanged);
    dojo.connect(dojo.byId('restfreq_setter'), 'onclick', restFrequencySet);
    dojo.connect(dojo.byId('restfreq_selection'), 'onchange', observationChanged);
    dojo.connect(dojo.byId('selfgen_selection'), 'onclick', reductionChanged);
    dojo.connect(dojo.byId('rfi_selection'), 'onclick', reductionChanged);
    dojo.connect(dojo.byId('edge_selection'), 'onchange', reductionChanged);

    observationChanged();
    reductionChanged();

    // Close everything except the first panel.
    manageProgress();

    var resultsReceived = function(data, ioargs) {
	manageProgress(true);
	// Check for the presence of specific zoom mode data.
	var specZoom = false;
	if (typeof data.specific_zoom !== 'undefined') {
	    specZoom = true;
	    dojo.removeClass('specific_zoom_region', 'hidden');
	    dojo.removeClass('specific_zoom_synthesised', 'hidden');
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
	// Hide elements that didn't get filled.
	dojo.query('.results').forEach(function(a, ai, al) {
		if (dojo.attr(a, 'innerHTML') === '') {
		    dojo.addClass(a.parentNode, 'hidden');
		} else {
		    dojo.removeClass(a.parentNode, 'hidden');
		}
	    });
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
	if (dojo.hasClass('fourcm_stuff', 'hidden') === false) {
	    params.fourcm = dojo.attr('fourcm_selection', 'value');
	}
	if (dojo.byId('selfgen_selection').checked) {
	    params.selfgen = 1;
	}
	if (dojo.byId('rfi_selection').checked) {
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

    dojo.connect(dojo.byId('calcsens_button'), 'onclick', calculate);

};

dojo.addOnLoad(init);
