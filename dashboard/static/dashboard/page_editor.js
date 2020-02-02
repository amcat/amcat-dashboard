"use strict";

define(["jquery", "pnotify", "bootstrap-multiselect", "jquery.cookie", "query/utils/format"], function($, PNotify){
    return function(opts){
        // Options
        var $container     = opts.container;
        var $rowTemplate   = opts.rowTemplate;
        var $colTemplate   = opts.rowTemplate.find(".col");
        var pageData       = opts.page;
        var synchroniseUrl = opts.synchroniseUrl;
        var saveUrl        = opts.saveUrl;

        // Button elements
        var $save        = $container.find(".save");
        var $preview     = $container.find(".preview");
        var $synchronise = $container.find(".synchronise");
        var $autoresize  = $container.find(".autoresize");
        var $addRow      = $container.find(".add-row");

        // Columns
        var bootstrapColums = [
            'col-sm-1', 'col-sm-2', 'col-sm-3', 'col-sm-4',
            'col-sm-5', 'col-sm-6', 'col-sm-7', 'col-sm-8',
            'col-sm-9', 'col-sm-10', 'col-sm-11', 'col-sm-12'
        ];

        /**
         * Convert bootstrap column string (col-lg-12) to a number
         * @returns column size
         */
        var colToNum = function(classes){
            var nums = $(classes.split(" ")).filter(function(index, cls){
                return $.inArray(cls, bootstrapColums) !== -1;
            });
            return parseInt(nums.get(0).split("-")[2]);
        };

        /**
         * Inverse of colToNum. Given a number, yield a bootstrap column class.
         */
        var numToCol = function(num){
            return "col-sm-" + num.toString();
        };

        var serialiseCell = function(cell){
            const customize = {};
            for(let formfield of $(cell).find('form.customize')[0].elements){
                if(formfield.name.length > 0 && formfield.value.length > 0){
                    let value = formfield.value;
                    if(formfield.type === "checkbox") {
                        value = formfield.checked;
                    }
                    customize[formfield.name] = value;
                }
            }

            console.debug("Customization parameters: ", customize);
            return {
                title: $(cell).find(".query-title").val(),
                width: colToNum($(cell).attr("class")),
                query_id: $(cell).find(".saved-query").val(),
                theme_id: $(cell).find("select.theme").val(),
                refresh_interval: $(cell).find("select.refresh-interval").val(),
                link: $(cell).find(".link").val(),
                customize: customize
            };
        };

        var serialiseRow = function(row){
            return [$.map($(row).find(".col"), serialiseCell)];
        };

        var _newCol = function(width, queryId, title, themeId, refreshInterval, customize, link){
            var newCol = $colTemplate.clone().show();
            var themeSelect = newCol.find(".theme");
            var querySelect = newCol.find(".saved-query");
            var linkInput = newCol.find(".link");
            var titleInput = newCol.find(".query-title");
            var refreshSelect = newCol.find(".refresh-interval");

            newCol.removeClass(bootstrapColums.join(" "));
            newCol.addClass(numToCol(width));
            $([themeSelect, querySelect, refreshSelect, linkInput]).addClass("multiselect-orig").multiselect({
                buttonClass: "btn btn-default btn-xs multiselect dropdown-toggle",
                buttonTitle: (options, select) => select[0].title
            });

            // Set default value for query
            if (refreshInterval !== undefined){
                refreshSelect.val(refreshInterval).multiselect("rebuild");
            }
            if (queryId !== undefined){
                querySelect.val(queryId).multiselect("rebuild");
            }
            if (link !== undefined) {
                linkInput.val(link);
            }

            if (title !== undefined){
                titleInput.val(title);
            }

            if(themeId !== undefined && themeId !== null){
                themeSelect.val(themeId).multiselect("rebuild");
            }

            if(typeof customize !== "object"){
                customize = {};
            }
            const form = newCol.find('form.customize');

            for(let el of form[0].elements){
                if(!customize.hasOwnProperty(el.name)){
                    continue;
                }
                if(el.type === "checkbox"){
                    el.checked = customize[el.name];
                }
                else{
                    el.value = customize[el.name];
                }
            }

            return newCol;
        };

        /** EVENTS **/
        var addRow = function(){
            var newRow = $("<div class='query-row row'>").hide().append(_newCol(12));
            $addRow.before(newRow);
            newRow.show("fast");
            initQueryButtons(newRow.find(".col"));
        };

        var addCol = function(){
            var currentWidth = colToNum(this.col.attr('class'));
            var newWidth = Math.floor(currentWidth / 2);

            if (newWidth < 2){
                return;
            }

            // Set new width on old cell
            this.col.removeClass(bootstrapColums.join(" "));
            this.col.addClass(numToCol(newWidth));

            // Set width on new cell
            var newCol = _newCol(currentWidth - newWidth);

            // Add new cell to either left or right side of existing one
            if (this.position === "left"){
                this.col.before(newCol);
            } else {
                this.col.after(newCol);
            }

            initQueryButtons(newCol);
        };

        var save = function(){
            var page = $.map($container.find(".query-row"), serialiseRow);
            $save.addClass("disabled").find("i").addClass("fa-spin");

            $.ajax({
                url: saveUrl,
                type: "post",
                data: JSON.stringify(page),
                contentType: "application/json",
                headers: {
                    "X-CSRFTOKEN": $.cookie(CSRF_COOKIE_NAME)
                }
            }).done(function () {
                $save.removeClass("disabled").find("i").removeClass("fa-spin");
                $save.addClass("btn-success").find("i").addClass("glyphicon-ok").removeClass('glyphicon-floppy-disk');

                setTimeout(() => $save
                    .removeClass("btn-success")
                    .find("i")
                    .removeClass("glyphicon-ok")
                    .addClass('glyphicon-floppy-disk'), 1000);

                new PNotify({text: "Saving OK", type: "success", delay: 200})
            }).fail(function () {
                $save.removeClass("disabled").find("i").removeClass("fa-spin");
                new PNotify({text: "Saving failed", type: "error"})
            })
        };

        var synchronise = function(){
            $synchronise.addClass("disabled").find("i").addClass("fa-spin");

            $.get(synchroniseUrl).done(function(queries){
                // TODO: Synchronise with existing buttons
                $synchronise.removeClass("disabled").find("i").removeClass("fa-spin");
                new PNotify({text: "Queries synchronised. Reload page to view changes.", type: "success", delay: 1500})
            }).fail(function(){
                $synchronise.removeClass("disabled").find("i").removeClass("fa-spin");
                new PNotify({text: "Synchronising failed", type: "error"})
            });
        };

        var delete_ = function(){
            var $sibling = this.siblings().first();

            // Remove whole row if we're the only one left
            if (!$sibling.length){
                this.closest(".row").remove();
                return;
            }

            // Remove yourself, and choose on of the siblings to expand 'into'
            // the old place
            var ownSize = colToNum(this.attr('class'));
            var siblingSize = colToNum($sibling.attr('class'));

            this.remove();

            $sibling.removeClass(bootstrapColums.join(" ")).addClass(numToCol(siblingSize + ownSize))

        };

        /**
         * Initialise buttons on a query
         */
        var initQueryButtons = function(col){
            col.find(".add-left").click(addCol.bind({col: col, position: "left"}));
            col.find(".add-right").click(addCol.bind({col: col, position: "right"}));
            col.find(".delete").click(delete_.bind(col));
        };

        var initButtons = function(){
            $addRow.click(addRow);
            $save.click(save);
            $synchronise.click(synchronise);
        };

        var initPage = function(){
            var rows = $.map(pageData.rows, function(row){
                return $("<div class='query-row row'>").append(
                    $.map(row, function(col){
                        var newCol = _newCol(col.width, col.query_id, col.title, col.theme_id, col.refresh_interval, col.customize, col.link);
                        initQueryButtons(newCol);
                        return newCol;
                    })
                );
            });

            $addRow.before(rows);
        };

        var init = function(){
            initButtons();
            initPage();
        };

        init();
    }
});