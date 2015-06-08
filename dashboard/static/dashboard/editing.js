"use strict";

define(["jquery", "bootstrap-multiselect"], function($){
    return function(opts){
        // Options
        var $container   = opts.container;
        var $pageData    = opts.page;
        var $rowTemplate = opts.rowTemplate;
        var $colTemplate = opts.rowTemplate.find(".col");

        // Button elements
        var $save        = $container.find(".save");
        var $preview     = $container.find(".preview");
        var $synchronise = $container.find(".synchronise");
        var $autoresize  = $container.find(".autoresize");
        var $addRow      = $container.find(".add-row");

        // Columns
        var bootstrapColums = [
            'col-lg-1', 'col-lg-2', 'col-lg-3', 'col-lg-4',
            'col-lg-5', 'col-lg-6', 'col-lg-7', 'col-lg-8',
            'col-lg-9', 'col-lg-10', 'col-lg-11', 'col-lg-12'
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
            return "col-lg-" + num.toString();
        };

        /** EVENTS **/
        var addRow = function(){
            var newRow = $rowTemplate.clone();
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
            var newCol = $colTemplate.clone().show();
            newCol.removeClass(bootstrapColums.join(" "));
            newCol.addClass(numToCol(currentWidth - newWidth));

            // Add new cell to either left or right side of existing one
            if (this.position === "left"){
                this.col.before(newCol);
            } else {
                this.col.after(newCol);
            }

            initQueryButtons(newCol);
        };

        /**
         * Initialise buttons on a query
         */
        var initQueryButtons = function(col){
            col.find(".add-left").click(addCol.bind({col: col, position: "left"}));
            col.find(".add-right").click(addCol.bind({col: col, position: "right"}));
        };

        var initButtons = function(){
            $addRow.click(addRow);
        };

        var init = function(){
            initButtons();
            $addRow.click();
        };

        init();
    }
});