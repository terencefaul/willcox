odoo.define('mediswitch_integration.new', function (require) {
"use strict";

	var rpc = require('web.rpc');
	var ListController = require('web.ListController');

ListController.include({
    renderButtons: function () {
        var self = this;
        this._super.apply(this, arguments);
        this.$buttons.on('click', '.global_fetch', function () {
            rpc.query({
                model: 'global.fetch.claim',
                method: 'create_global_fetch_record',
                args:[],
            },{
                async: false
            }).then(function(id){
                self.do_action({
                    name: 'GLobal Fetch Claim Wizard',
                    res_model: 'global.fetch.claim',
                    views: [[id || false, 'form']],
                    type: 'ir.actions.act_window',
                    target:'new',
                });
            });
        });
    }
});

});