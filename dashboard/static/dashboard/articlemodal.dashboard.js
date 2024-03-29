"use strict";
/**************************************************************************
*          (C) Vrije Universiteit, Amsterdam (the Netherlands)            *
*                                                                         *
* This file is part of AmCAT - The Amsterdam Content Analysis Toolkit     *
*                                                                         *
* AmCAT is free software: you can redistribute it and/or modify it under  *
* the terms of the GNU Affero General Public License as published by the  *
* Free Software Foundation, either version 3 of the License, or (at your  *
* option) any later version.                                              *
*                                                                         *
* AmCAT is distributed in the hope that it will be useful, but WITHOUT    *
* ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or   *
* FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public     *
* License for more details.                                               *
*                                                                         *
* You should have received a copy of the GNU Affero General Public        *
* License along with AmCAT.  If not, see <http://www.gnu.org/licenses/>.  *
***************************************************************************/
define([
    "jquery", "query/utils/elasticfilters", "query/valuerenderers", "bootstrap",
    "amcat-common/amcat.datatables"],
    function($, elastic_filters, value_renderers){
    var defaults = {
        "modal": "#articlelist-dialog",
        "search_api_url": `/dashboard/systems/${DASHBOARD_SYSTEM.id}/search`,
        "article_url_format": `${DASHBOARD_SYSTEM.hostname}/projects/${DASHBOARD_SYSTEM.project_id}/articles/{id}`
    };

    return function(userOptions){
        var options = $.extend({}, $.extend(defaults, userOptions));
        var $modal = $(options.modal);

        /**
         * Renders popup with a list of articles, based on given filters.
         * @param filters mapping { type -> filter }. For example:
         *        { medium : 1, date: 1402005600000 }
         */
        function articles_popup(form_data, filters){
            var data = $.extend({}, form_data);

            $.each(filters, function(type, value){
                if (elastic_filters[type] !== undefined){
                    // Use elastic mapping function
                    $.extend(data, elastic_filters[type](form_data, value, data));
                } else {
                    // Store raw data as filter
                    data[type] = value;
                }
            });

            // HACK: If a specific set is requested by a user (by clicking on a table cell,
            // for example), override global articleset filter.
            if (filters.set !== undefined){
                delete data["articlesets"];
            }

            var table = $modal.find(".articlelist").find(".dataTables_scrollBody table");

            if (table.length > 0){
                table.DataTable().destroy();
            }

            amcat.datatables.create_rest_table(
                $modal.find(".articlelist").html(""),
                options.search_api_url + "?" + $.param(getSearchFilters(data, filters), true),
                {
                    "setup_callback": function(tbl){
                        tbl.fnSetRowlink(options.article_url_format, "new");
                    },
                    datatables_options: {iDisplayLength: 10,  aaSorting: []},

                    onFetchedInitialError(jqXHR, statusText, errorThrown){
                        console.error(JSON.parse(jqXHR.responseText));
                        container.html("").append(
                            $(`<p class="text-danger">Error fetching articles: ${errorThrown}.</p>`),
                            $(`<p class="text-danger">Reason: ${JSON.parse(jqXHR.responseText).message}</p>`)
                        )
                    }
                }
            )
        }

        /**
         * Convert form field / values to their search API counterpart. For
         * example:
         *     mediums -> mediumid
         *     query -> q
         * @param data
         */
        function getSearchFilters(data, filters){
            var new_filters = {};
            var field_map = {
                query: "q", article_ids: "ids",
                start_date: "start_date", end_date: "end_date",
                articlesets: "sets", sets: "sets", on_date: "on_date",
                project: "project", relative_date: "relative_date"
            };

            var value_map = {
                ids: function(aids){ return $.map(aids.split("\n"), $.trim); },
                start_date: value_renderers.date,
                end_date: value_renderers.date
            };

            $.each(field_map, function(k, v){
                if (data[k] === null || data[k] === undefined || data[k] === ""){
                    return;
                }

                new_filters[v] = data[k];
                if (value_map[v] !== undefined){
                    new_filters[v] = value_map[v](new_filters[v]);
                }
            });

            if(new_filters["q"] && filters["term"]){
                new_filters["q"] = filters["term"];
                delete filters["term"];
            }
            return $.extend({}, new_filters, filters);
        }

        return {
            /**
             * Show article popup with given filters applied.
             *
             * @param filters: mapping of type -> value.
             */
            show: function(form_data, filters){
                filters = (filters === undefined) ? {} : filters;
                articles_popup(form_data, filters);
                $modal.modal("show");
            },
            hide: function(){
                $modal.modal("hide");
            }
        }
    }
});
