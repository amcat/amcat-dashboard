"use strict";

define(["jquery", "bootstrap-switch"], function($){
    return function(opts){
        var $menu          = opts.menu;
        var $menuTemplate  = opts.menuTemplate;
        var $globalOptions = $("#global-options");
        var $add           = $globalOptions.find('.add-page');
        var $save          = $globalOptions.find('.save');

        var addItem = function(name, visible, pageId){
            var newItem = $menuTemplate.clone();
            $menu.append(newItem);
            newItem.show("fast");

            // Fill name property if possible
            if (name !== undefined){
                newItem.find("[name=name]").val(name);
            }

            // Check visible checkbox if needed
            if (visible !== undefined && visible){
                newItem.find("[name=visible]").prop("checked", "checked");
            }

            newItem.data("page-id", pageId);

            initButtons(newItem);
        };

        var moveDown = function(){
            if (!this.next().length) return;
            this.insertAfter(this.next());
        };

        var moveUp = function(){
            if (!this.prev().length) return;
            this.insertBefore(this.prev());
        };

        var delete_ = function(){
            this.remove();
        };

        var initButtons = function(item){
            item.find(".move-down").click(moveDown.bind(item));
            item.find(".move-up").click(moveUp.bind(item));
            item.find(".delete").click(delete_.bind(item));
            item.find(".page-visible").bootstrapSwitch();
        };

        var init = function(){
            $add.click(function(){ addItem(); });
        };

        init();
    };
});