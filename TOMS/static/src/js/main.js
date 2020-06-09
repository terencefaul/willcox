odoo.define('TOMS.TOMS', function(require) {
    "use strict";

    var FormRenderer = require('web.FormRenderer');
    var FormController = require('web.FormController');
    var CalendarRenderer = require('web.CalendarRenderer')
    var weContext = require('web_editor.context');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var BasicController = require('web.BasicController')
    var ListRenderer = require('web.ListRenderer')
    var field_utils = require('web.field_utils');
    var BasicFields = require('web.basic_fields')
    var _t = core._t;

    var FIELD_CLASSES = {
        float: 'o_list_number',
        integer: 'o_list_number',
        monetary: 'o_list_number',
        text: 'o_list_text',
    };
//    CalendarRenderer.include({
//    });


    BasicFields.NumericField.include({
        _formatValue: function (value) {
        if (this.mode === 'edit' && this.nodeOptions.type === 'number') {
            return value;
        }
        var field_list = ['pupil_heights_r','pupil_heights_l','mono_r','mono_l','seg_heights_r','seg_heights_l','pd_r','pd_l','od_cyl','od_syh','os_syh','os_cyl']
        if(this.$el.find('toms_form_number')){
            if(value != 0 && !(value.toString()).includes('-') && $.inArray(this.$el.attr('name').trim(),field_list) != -1){
                return "+"+value.toFixed(2).toString()
            }
        }
        return this._super.apply(this, arguments);
    },
    });

    ListRenderer.include({
        _renderBodyCell: function (record, node, colIndex, options) {
            var tdClassName = 'o_data_cell';
            if (node.tag === 'button') {
                tdClassName += ' o_list_button';
            } else if (node.tag === 'field') {
                var typeClass = FIELD_CLASSES[this.state.fields[node.attrs.name].type];
                if (typeClass) {
                    tdClassName += (' ' + typeClass);
                }
                if (node.attrs.widget) {
                    tdClassName += (' o_' + node.attrs.widget + '_cell');
                }
            }
            var $td = $('<td>', { class: tdClassName });

            // We register modifiers on the <td> element so that it gets the correct
            // modifiers classes (for styling)
            var modifiers = this._registerModifiers(node, record, $td, _.pick(options, 'mode'));
            // If the invisible modifiers is true, the <td> element is left empty.
            // Indeed, if the modifiers was to change the whole cell would be
            // rerendered anyway.
            if (modifiers.invisible && !(options && options.renderInvisible)) {
                return $td;
            }

            if (node.tag === 'button') {
                return $td.append(this._renderButton(record, node));
            } else if (node.tag === 'widget') {
                return $td.append(this._renderWidget(record, node));
            }
            if (node.attrs.widget || (options && options.renderWidgets)) {
                var $el = this._renderFieldWidget(node, record, _.pick(options, 'mode'));
                this._handleAttributes($el, node);
                return $td.append($el);
            }
            var name = node.attrs.name;
            var field = this.state.fields[name];
            var value = record.data[name];
            var formattedValue = field_utils.format[field.type](value, field, {
                data: record.data,
                escape: true,
                isPassword: 'password' in node.attrs,
            });
            this._handleAttributes($td, node);
            if($td.hasClass('number_value') && !formattedValue.includes('-') && formattedValue != '0.00' && formattedValue != ''){
                return $td.html("+"+formattedValue);
            }
            return $td.html(formattedValue);
        },
    });

    BasicController.prototype._callButtonAction = function(attrs, record){
        var self = this;
        if(attrs.name == 'refresh_examination' && record.model == 'clinical.examination'){
            self.update({});
            setTimeout(function(){
                $('.o_form_button_edit').trigger('click');
            }, 100)
        }else{
            var def = $.Deferred();
            var reload = function () {
                return self.isDestroyed() ? $.when() : self.reload();
            };
            record = record || this.model.get(this.handle);

            this.trigger_up('execute_action', {
                action_data: _.extend({}, attrs, {
                    context: record.getContext({additionalContext: attrs.context || {}}),
                }),
                env: {
                    context: record.getContext(),
                    currentID: record.data.id,
                    model: record.model,
                    resIDs: record.res_ids,
                },
                on_closed: function (reason) {
                    if (!_.isObject(reason)) {
                        reload(reason);
                    }
                },
                on_fail: function (reason) {
                    reload().always(function() {
                        def.reject(reason);
                    });
                },
                on_success: def.resolve.bind(def),
            });
            return this.alive(def);
        }
    };

    

});