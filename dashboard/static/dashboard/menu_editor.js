"use strict";

define(["jquery", "pnotify", "jquery.cookie", "bootstrap-switch"], function($, PNotify){
    return function(opts){
        var $menu          = opts.menu;
        var $menuTemplate  = opts.menuTemplate;
        var $globalOptions = $("#global-options");
        var $add           = $globalOptions.find('.add-page');
        var $save          = $globalOptions.find('.save');

        var pageData       = opts.pageData;
        var saveUrl        = opts.saveUrl;

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

        var serializePage = function($page){
            return {
                id: $page.data("page-id") || null,
                name: $page.find("[name=name]").val(),
                visible: $page.find("[name=visible]").prop("checked"),
                icon: ""
            }
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

        var createCopy = function(){
            save();

        };

        var save = function(){
            var $pages = $.map($("#side-menu").find(".menu-template"), $);
            var pageData = $.map($pages, serializePage);

            $.ajax({
                data: JSON.stringify(pageData),
                url: saveUrl,
                type: "post",
                contentType: "application/json",
                headers: {
                    "X-CSRFTOKEN": $.cookie(CSRF_COOKIE_NAME)
                }
            }).done(function(){
                new PNotify({text: "Menu saved.", type: "success", delay: 1500});
            }).fail(function(){
                new PNotify({text: "Saving failed.", type: "error"});
            });
        };

        var initButtons = function(item){
            item.find(".move-down").click(moveDown.bind(item));
            item.find(".move-up").click(moveUp.bind(item));
            item.find(".delete").click(delete_.bind(item));
            item.find(".create-copy").click(createCopy.bind(item));
            item.find(".page-visible").bootstrapSwitch();
        };

        var init = function(){
            $add.click(function(){ addItem(); });
            $save.click(function(){ save(); });

            $.map(pageData, function(page){
                addItem(page.name, page.visible, page.id);
            })
        };

        init();
    };
});