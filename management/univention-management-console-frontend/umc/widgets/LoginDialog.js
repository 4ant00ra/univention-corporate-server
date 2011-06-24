/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.LoginDialog");

dojo.require("dijit.form.Button");
dojo.require("dijit.form.TextBox");
dojo.require("dijit.layout.ContentPane");
dojo.require("dojox.widget.Dialog");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.ContainerForm");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.widgets.Text");

dojo.declare('umc.widgets.LoginDialog', [ dojox.widget.Dialog, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	// our own variables
	_container: null,
	_passwordTextBox: null,
	_usernameTextBox: null,
	_form: null,
	_container: null,

	// use the framework wide translation file
	i18nClass: 'umc.app',

	postMixInProperties: function() {
		dojo.mixin(this, {
			closable: false,
			modal: true,
			sizeDuration: 900,
			sizeMethod: 'chain',
			sizeToViewport: false,
			dimensions: [300, 280]
		});

	},

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'TextBox',
			name: 'username',
			value: dojo.cookie('UMCUsername') || '',
			description: this._('The username of your domain account.'),
			label: this._('Username')
		}, {
			type: 'PasswordBox',
			name: 'password',
			description: this._('The password of your domain account.'),
			label: this._('Password')
		}, {
			type: 'ComboBox',
			name: 'language',
			staticValues: [
				{ id: 'de', label: this._('German') },
				{ id: 'en', label: this._('English') }
			],
			value: dojo.locale.substring(0, 2),
			description: this._('The language for the login session.'),
			label: this._('Language')
		}];

		var buttons = [{
			name: 'submit',
			label: this._('Login'),
			callback: dojo.hitch(this, function(values) {
				// call LoginDialog.onSubmit() and clear password
				this._authenticate(values.username, values.password);
				this._form.elementValue('password', '');
			})
		}, {
			name: 'cancel',
			label: this._('Reset')
		}];

		var layout = [['username'], ['password'], ['language']];
		 
		this._form = new umc.widgets.Form({
			//style: 'width: 100%',
			widgets: widgets,
			buttons: buttons,
			layout: layout,
			style: 'margin-left: auto; margin-right: auto; width: 180px;'
		}).placeAt(this.containerNode);
		this._form.startup();

		// register onChange event
		this.connect(this._form._widgets.language, 'onChange', function() {
			// reload the page when a different language is selected
			var query = dojo.queryToObject(window.location.search.substring(1));
			query.lang = this._form.elementValue('language');
			dojo.cookie('UMCLang', query.lang, { expires: 100, path: '/' });
			window.location.search = '?' + dojo.objectToQuery(query);
		});

		// put the layout together
		this._container = new umc.widgets.ContainerWidget({});
		this._container.addChild(new umc.widgets.Text({
			style: 'margin-left: auto; margin-right: auto; width: 250px;',
			content: '<p>' + this._('Welcome to the Univention Management Console. Please enter your domain username and password for login!') + '</p>'
		}));
		this._container.addChild(this._form);
		this.set('content', this._container);
	},

	postCreate: function() {
		// call superclass' postCreate()
		this.inherited(arguments);

		// hide the close button
		dojo.style(this.closeButtonNode, 'display', 'none');
	},

	_showContent: function() {
		this.inherited(arguments);

		// focus on password input field if username is already given by cookie
		if (this._form.elementValue('username')) {
			this._form._widgets.password.focus();
		}
	},

	reset: function() {
		// description:
		//		Reset all form entries to their initial values.
		this._passwordTextBox.reset();
		this._usernameTextBox.reset();
	},

	_onKey:  function(evt) {
		// ignore ESC key
		if (evt.charOrCode == dojo.keys.ESCAPE) {
			return;
		}

		// otherwise call the standard handler
		this.inherited(arguments);
	},

	_authenticate: function(username, password) {
		this.standby(true);
		umc.tools.umcpCommand('auth', {
			username: username,
			password: password
		}).then(dojo.hitch(this, function(data) {
			// disable standby in any case
			//console.log('# _authenticate - ok');
			//console.log(data);
			this.standby(false);

			// make sure that we got data
			this.onLogin(username);
		}), dojo.hitch(this, function(error) {
			// disable standby in any case
			//console.log('# _authenticate - error');
			//console.log(error);
			this.standby(false);
		}));
	},

	onLogin: function(/*String*/ username) {
		// event stub
	}
});


