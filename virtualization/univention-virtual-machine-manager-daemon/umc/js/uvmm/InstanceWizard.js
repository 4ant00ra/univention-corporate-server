/*
 * Copyright 2014 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/event",
	"dojo/keys",
	"umc/widgets/TextBox",
	"umc/widgets/Text",
	"umc/widgets/ComboBox",
	"umc/widgets/HiddenInput",
	"umc/widgets/Wizard",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, event, keys, TextBox, Text, ComboBox, HiddenInput, Wizard, types, _) {

	return declare("umc.modules.uvmm.InstanceWizard", [ Wizard ], {
		autoValidate: true,

		_size_id: null,
		
		cloud: null,

		constructor: function(props) {
			this.inherited(arguments);
			// mixin the page structure
			this.cloud = props.cloud;
			lang.mixin(this, {
				pages: this.getPages(),
				headerButtons: [{
					name: 'close',
					iconClass: 'umcCloseIconWhite',
					label: _('Back to overview'),
					callback: lang.hitch(this, 'onCancel')
				}]
			});
		},

		_getHelpText: function() {
			if (this.cloud.type == 'OpenStack') {
				return _('Please enter the corresponding details for the virtual machine instance.');
			} else if (this.cloud.type == 'EC2') {
				return _('Please enter the corresponding details for the virtual machine instance. <a href="https://aws.amazon.com/documentation/ec2/" target=_blank>Use this link for more information about Amazon EC2</a>');
			}
		},

		getPages: function() {
			var content = this._getWidgets();
			var helpText = this._getHelpText();
			return [{
				name: 'details',
				headerText: _('Create a new virtual machine instance.'),
				helpText: helpText,
				widgets: content.widgets,
				buttons: content.buttons,
				layout: content.layout
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);
			// store umcp response of "size_id" for updating "size_info_text"
			var widget = this.getWidget('details', 'size_id');
			widget.on('dynamicValuesLoaded', lang.hitch(this, function(value) {
				this._size_id = value;
				this._update_size_info_text(value[0].id);
			}));
		},

		_get_size_id: function(newVal) {
			var value = array.filter(this._size_id, function(item) {
				return item.id == newVal;
			});
			if (!value.length) {
				return null;
			}
			return value[0];
		},
		_update_size_info_text: function(newVal) {
			var widget = this.getWidget('details', 'size_info_text');
			var size = this._get_size_id(newVal);
			if (size) {
				var text = '';
				if (size.vcpus !== null) {
					text += _('Number of CPUs') + ': ' + size.vcpus + ', ';
				}
				text += _('Memory') + ': ' + size.ram + ' MB, ';
				text += _('Hard drive') + ': ' + size.disk + ' GB ';
				widget.set('content', '<p>' + text + '</p>');
			}
		},

		_getWidgets: function() {
			if (this.cloud.type == 'OpenStack') {
				return {
					layout: [
						'name',
						'image_id',
						'size_id',
						'size_info_text',
						['keyname', 'security_group_ids']
						
					],
					widgets: [{
						name: 'cloudtype',
						type: HiddenInput,
						value: this.cloud.type
					}, {
						name: 'cloud',
						type: HiddenInput,
						value: this.cloud.name
					}, {
						name: 'name',
						type: TextBox,
						label: _('Instance Name'),
						required: true,
						size: 'Two'
					}, {
						name: 'keyname',
						type: ComboBox,
						label: _('Select a key pair'),
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListKeypair,
						required: true
					}, {
						name: 'image_id',
						type: ComboBox,
						label: _('Choose an Image'),
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: lang.hitch(this, function(options) {
							return this.standbyDuring(types.getCloudListImage(options));
						}),
						required: true,
						size: 'Two'
					}, {
						name: 'size_id',
						type: ComboBox,
						label: _('Choose an Instance Size'),
						sortDynamicValues: false,
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListSize,
						required: true,
						size: 'Two',
						onChange: lang.hitch(this, function(newVal) {
							this._update_size_info_text(newVal);
						})
					}, {
						type: Text,
						name: 'size_info_text',
						content: '',
						label: '&nbsp;'
					}, {
						name: 'security_group_ids',
						type: ComboBox,
						label: _('Configure Security Group'),
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListSecgroup,
						required: true
					}]
				};
			}
			if (this.cloud.type == 'EC2') {
				var filterOptions = [];
				if (this.cloud.showUnivention) {
					filterOptions.push({ id: 'univention', label: _('Show only Univention AMIs') });
				}
				if (this.cloud.preSelection.length) {
					filterOptions.push({ id: 'preselection', label: _('Select AMI from a predefined set') });
				}
				if (this.cloud.allowsSearch) {
					filterOptions.push({ id: 'search', label: _('Search all available AMIs') });
				}
				var defaultFilterOption = null;
				if (filterOptions.length) {
					defaultFilterOption = filterOptions[0].id;
				}
				return {
					layout: [
						'name',
						'image_filter',
						['image_filter_search', 'image_filter_search_submit'],
						'image_id',
						'size_id',
						'size_info_text',
						['keyname', 'security_group_ids']
					],
					widgets: [{
						name: 'cloudtype',
						type: HiddenInput,
						value: this.cloud.type
					}, {
						name: 'cloud',
						type: HiddenInput,
						value: this.cloud.name
					}, {
						name: 'name',
						type: TextBox,
						label: _('Instance Name'),
						required: true,
						size: 'Two'
					}, {
						name: 'keyname',
						type: ComboBox,
						label: _('Select a key pair'),
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListKeypair,
						required: true
					}, {
						name: 'size_id',
						type: ComboBox,
						label: _('Choose an Instance Size'),
						sortDynamicValues: false,
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListSize,
						required: true,
						size: 'Two',
						onChange: lang.hitch(this, function(newVal) {
							this._update_size_info_text(newVal);
						})
					}, {
						type: Text,
						name: 'size_info_text',
						content: '',
						label: '&nbsp;'
					}, {
						name: 'image_id',
						type: ComboBox,
						label: _('Search for and choose an AMI'),
						sortDynamicValues: false,
						dynamicOptions: this._ec2ImageDynamicOptions(defaultFilterOption),
						dynamicValues: lang.hitch(this, function(options) {
							return this.standbyDuring(types.getCloudListImage(options));
						}),
						required: true,
						size: 'Two'
					}, {
						name: 'image_filter',
						type: ComboBox,
						staticValues: filterOptions,
						label: _('Filter AMIs'),
						onChange: lang.hitch(this, function(newVal) {
							var widget = this.getWidget('details', 'image_id');
							var imageSearch = this.getWidget('details', 'image_filter_search');
							var imageSearchButton = this.getPage('details')._form.getButton('image_filter_search_submit');
							imageSearch.set('visible', false);
							imageSearchButton.set('visible', false);

							var options = this._ec2ImageDynamicOptions(newVal);
							if (newVal != 'search') {
								widget.set('dynamicOptions', options);
							}
						})
					}, {
						name: 'image_filter_search',
						type: TextBox,
						label: _('Search pattern'),
						onKeyDown: lang.hitch(this, function(e) {
							if (e.keyCode == keys.ENTER) {
								this.filterAMIs();
								e.preventDefault();
								event.stop(e);
							}
						}),
						visible: false
					}, {
						name: 'security_group_ids',
						type: ComboBox,
						label: _('Configure Security Group'),
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListSecgroup,
						required: true
					}],
					buttons: [{
						name: 'image_filter_search_submit',
						label: _('Search'),
						visible: false,
						style: 'position: relative; bottom: 2.4em;',
						callback: lang.hitch(this, 'filterAMIs')
					}]
				};
			}
			return {};
		},

		_ec2ImageDynamicOptions: function(filterOption) {
			var options = {conn_name: this.cloud.name};
			if (filterOption == 'univention') {
				options.ucs_images = true;
			} else if (filterOption == 'preselection') {
				options.onlypreselected = true;
			} else if (filterOption == 'search') {
				var imageSearch = this.getWidget('details', 'image_filter_search');
				var imageSearchButton = this.getPage('details')._form.getButton('image_filter_search_submit');
				imageSearch.set('visible', true);
				imageSearchButton.set('visible', true);
				var value = imageSearch.get('value');
				if (value) {
					options.pattern = value;
				}
			}
			return options;
		},

		filterAMIs: function() {
			var widget = this.getWidget('details', 'image_id');
			var options = this._ec2ImageDynamicOptions('search');
			widget.set('dynamicOptions', options);
		},

		onFinished: function() {
			// event stub
		}
	});
});
