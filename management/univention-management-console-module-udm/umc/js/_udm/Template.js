/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._udm.Template");

dojo.declare('umc.modules._udm.Template', null, {
	// summary:
	//		Class that provides a template functionality for UDM objects.
	// description:
	//		This class registers event handlers and monitors user input in order to
	//		update UDM object values for a specified template. Template values may
	//		be static values (i.e., strings) or values containing references to other
	//		form fields. References are indicated by using tags '<variable>'. 
	//		Additionally, modifiers can be applied to the content of a variable (e.g.,
	//		to convert values to upper or lower case) and an index operator enables
	//		accessing particular character ranges.
	// example:
	//		Here some valid examples for variable expansion.
	//	|	simple: 
	//	|	  <var>               -> 'Univention'
	//	|	with modifiers: 
	//	|	  <var:lower>         -> 'univention'
	//	|	  <var:upper>         -> 'UNIVENTION'
	//	|	  <var:umlauts,upper> -> 'UNIVENTION'
	//	|	with index operator: 
	//	|	  <var>[0]   -> 'U'
	//	|	  <var>[-2]  -> 'o'
	//	|	  <var>[0:2] -> 'Un'
	//	|	  <var>[1:]  -> 'nivention'
	//	|	  <var>[:3]  -> 'Uni'
	//	|	  <var>[:-3] -> 'Univent'
	//

	// widgets: Object
	//		Dict of (key -> widget) pairs containing all form widgets of 
	//		the edited object. 
	widgets: null,

	// template: Object
	//		Dict of (key -> value) pairs specifying template values for each UDM
	//		property.
	template: null,

	_inverseReferences: null,

	_userChanges: null,

	_eventHandles: null,

	_focusedWidget: '',

	// mappings to convert umlauts and special characters to standard ones
	_umlauts: { 'ä' :'ae', 'Ä' : 'Ae', 'ö' : 'oe', 'Ö' : 'Oe', 'ü' : 'ue', 'Ü' : 'Ue', 'ß' : 'ss', 'Á' : 'A', 'Â' : 'A', 'Ã' : 'A', 'Ä' : 'A', 'Å' : 'A', 'Æ' : 'AE', 'Ç' : 'C', 'È' : 'E', 'É' : 'E', 'Ê' : 'E', 'Ë' : 'E', 'Ì' : 'I', 'Í' : 'I', 'Î' : 'I', 'Ï' : 'I', 'Ð' : 'D', 'Ñ' : 'N', 'Ò' : 'O', 'Ó' : 'O', 'Ô' : 'O', 'Õ' : 'O', 'Ö' : 'O', 'Ù' : 'U', 'Ú' : 'U', 'Û' : 'U', 'à' : 'a', 'â' : 'a', 'á' : 'a', 'ã' : 'a', 'æ' : 'ae', 'ç' : 'c', 'è' : 'e', 'é' : 'e', 'ê' : 'e', 'ë' : 'e', 'ì' : 'i', 'í' : 'i', 'î' : 'i', 'ï' : 'i', 'ñ' : 'n', 'ò' : 'o', 'ó' : 'o', 'ô' : 'o', 'ù' : 'u', 'ú' : 'u', 'û' : 'u', 'ý' : 'y', 'ÿ' : 'y', 'Ĉ' : 'C', 'ĉ' : 'c' },

	// regular expression for matching variable references in the template
	_regVar: /<(\w+)(:([\w,]*))?>(\[(-?\d*)(:(-?\d*))?\])?/g,

	constructor: function(props) {
		// mixin the props
		dojo.mixin(this, props);

		// iterate over all template values
		// * set static values directly to the form
		// * register dynamic values to react on user input
		var updaters = [];
		umc.tools.forIn(this.template, function(ikey, ival) {
			// ignore values that do not have a widget
			if (!(ikey in this.widgets)) {
				console.log('WARNING: The property "' + ikey + '" as specified by the template does not exist. Ignoring error.');
				return true;
			}

			// object for updating the field
			var updater = {
				key: ikey,
				selfReference: this.widgets[ikey],
				templateString: dojo.clone(ival),
				references: [], // ordered list of widgets that are referenced
				modifiers: [], // ordered list of string modifiers per reference
				update: function() {
					// collect all necessary values
					var vals = [];
					dojo.forEach(this.references, function(iwidget, i) {
						vals.push(this.modifiers[i](iwidget.get('value')));
					}, this);

					// the value might be a simple string or an array of strings
					var newVal;
					if (dojo.isString(this.templateString)) {
						newVal = dojo.replace(this.templateString, vals);
					}
					else if (dojo.isArray(this.templateString)) {
						newVal = [];
						dojo.forEach(this.templateString, function(istr) {
							newVal.push(dojo.replace(istr, vals));
						});
					}

					// block onChange events (so we do not register the values as changes by
					// the user) and set the value
					//this.selfReference.set('blockOnChange', true);
					this.selfReference.set('value', newVal);
					//this.selfReference.set('blockOnChange', false);
				}
			};

			// try to match all variable references... the template value might be a string
			// or an array of strings
			var nRefs = 0;
			var tmpVals = dojo.isArray(ival) ? ival : [ival];
			dojo.forEach(tmpVals, function(jval, j) {
				var matches = jval.match(this._regVar);
				dojo.forEach(matches, function(imatch) {
					// parse the matched reference
					this._regVar.lastIndex = 0; // start matching in any case from the string beginning
					var match = this._regVar.exec(imatch);

					// we have a value with variable reference... 
					// parse the variable reference and get the correct indeces
					var refKey = match[1];
					var modifier = match[3];
					var startIdx = 0;
					var endIdx = Infinity;
					try {
						startIdx = !match[5] ? 0 : parseInt(match[5], 10);
					}
					catch (err1) { }

					// check whether the user specified an end index
					if (!match[6] && dojo.isString(match[5])) {
						// nope... index points to one single character
						endIdx = startIdx + 1;
						if (0 === endIdx) {
							// startIdx == -1
							endIdx = Infinity;
						}
					}
					else if (match[6]) {
						try {
							endIdx = !match[7] && match[7] !== '0' ? Infinity : parseInt(match[7], 10);
						}
						catch (err2) { }
					}

					// register the reference
					if (!(refKey in this.widgets)) {
						// reference does not exist
						return true;
					}
					updater.references.push(this.widgets[refKey]);

					// update the template string
					if (dojo.isArray(ival)) {
						updater.templateString[j] = updater.templateString[j].replace(imatch, '{' + nRefs + '}');
					}
					else {
						updater.templateString = updater.templateString.replace(imatch, '{' + nRefs + '}');
					}

					// register the modifier
					updater.modifiers.push(this._getModifiers(modifier, startIdx, endIdx));

					// count the matched references
					++nRefs;
				}, this);
			}, this);
			if (nRefs) {
				// we have a dynamic value with variable references
				updaters.push(updater);
			}
			else {
				// we have a static value, try to set the given key
				if (ikey in this.widgets) {
					this.widgets[ikey].set('value', ival);
				}
			}
		}, this);

		// build an inverse map to the reference... i.e., we want to know for a field
		// that is being changed, which other templated fields depend on its value
		this._inverseReferences = {};
		dojo.forEach(updaters, function(iupdater) {
			// get inverse references
			dojo.forEach(iupdater.references, function(iref) {
				// when we have the first entry for this reference, initiate with an empty dict
				if (!(iref.name in this._inverseReferences)) {
					this._inverseReferences[iref.name] = {};
				}

				// register the reference
				this._inverseReferences[iref.name][iupdater.key] = iupdater;
			}, this);

			// update field for the first time
			iupdater.update();
		}, this);

		// register user changes
		this._userChanges = {};
		this._eventHandles = [];
		umc.tools.forIn(this.widgets, function(ikey, iwidget) {
			// monitor value changes... onChange for changes made automatically and
			// onKeyUp for changes made by the user
			this._eventHandles.push(dojo.connect(iwidget, 'onKeyUp', dojo.hitch(this, 'onChange', iwidget)));
			this._eventHandles.push(dojo.connect(iwidget, 'onChange', dojo.hitch(this, 'onChange', iwidget)));
		}, this);
	},

	_getModifiers: function(modifierString, startIdx, endIdx) {
		// get the correct string modifiers (can be a list of modifiers)
		var modifierNames = dojo.isString(modifierString) ? modifierString.toLowerCase().split(',') : [''];
		var modifiers = [];
		dojo.forEach(modifierNames, function(iname) {
			switch(dojo.trim(iname)) {
			case 'lower': 
				modifiers.push(function(str) {
					return dojo.isString(str) ? str.toLowerCase() : str;
				});
				break;
			case 'upper': 
				modifiers.push(function(str) {
					return dojo.isString(str) ? str.toUpperCase() : str;
				});
				break;
			case 'umlaut':
			case 'umlauts':
				modifiers.push(dojo.hitch(this, function(str) {
					if (!dojo.isString(str)) {
						return str;
					}
					var newStr = '';
					for (var i = 0; i < str.length; ++i) {
						newStr += this._umlauts[str[i]] || str[i];
					}
					return newStr;
				}));
				break;
			default:
				// default modifier is a dummy function that does nothing
				modifiers.push(function(str) { return str; });
			}
		}, this);

		// add index operator as last modifier
		modifiers.push(function(str) {
			return str.slice(startIdx, endIdx);
		});

		// return function that applies all modifiers
		return function(str) {
			dojo.forEach(modifiers, function(imod) {
				str = imod(str);
			});
			return str;
		};
	},

	onChange: function(widget) {
		// register that the user has changed this field manually in case the
		// focus was on this field
		if (widget.get('focused')) {
			this._userChanges[widget.name] = true;
		}

		// see whether we can update other fields that have not been changed manually
		var references = this._inverseReferences[widget.name] || {};
		umc.tools.forIn(references, function(iRefKey, iUpdater) {
			if (!this._userChanges[iRefKey]) {
				iUpdater.update();
			}
		}, this);
	},

	destroy: function() {
		// when called, disconnect signal handlers
		dojo.forEach(this._eventHandles, dojo.disconnect);	
	}
});



