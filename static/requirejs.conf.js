requirejs.config({
    "baseUrl": "/static/components",
    "paths": {
        "query": "amcat-query/query",
        "jquery": "jquery/dist/jquery",
        "papaparse": "papaparse/papaparse",
        "highlight": "highlight/build/highlight.pack",
        "highcharts.core": "highcharts/highcharts.src",
        "highcharts.data": "highcharts/modules/data",
        "highcharts.exporting": "highcharts/modules/exporting",
        "highcharts.drilldown": "highcharts/modules/drilldown",
        "highcharts.heatmap": "highcharts/modules/heatmap",
        "bootstrap": "bootstrap/dist/js/bootstrap",
        "bootstrap-multiselect": "bootstrap-multiselect/dist/js/bootstrap-multiselect",
        "bootstrap-tooltip": "bootstrap/js/tooltip",
        "bootstrap-datepicker": "bootstrap-datepicker/dist/js/bootstrap-datepicker",
        "bootstrap-switch": "bootstrap-switch/dist/js/bootstrap-switch",
        "moment": "moment/moment",
        "moment-locale": "moment/locale",
        "renderjson": "renderjson/renderjson",
        "datatables": "datatables/media/js/jquery.dataTables",
        "datatables.tabletools": "datatables/extensions/TableTools/js/dataTables.tableTools",
        "jshashset": "jshashtable/hashset",
        "jshashtable": "jshashtable/hashtable",

        // load alternative articlemodal
        "query/utils/articlemodal": "../dashboard/articlemodal.dashboard",
        "query/utils/articlemodal.amcat": "amcat-query/query/utils/articlemodal",

        "amcat-common": "amcat-common/js",
        "jquery.cookie": "jquery-cookie/jquery.cookie",
        "metis-menu": "metisMenu/dist/metisMenu",
        "sb-admin": "startbootstrap-sb-admin-2/dist/js/sb-admin-2",
        "pnotify": "pnotify/dist/pnotify",
        "pnotify.nonblock": "pnotify/dist/pnotify.nonblock",
        "dashboard": "../dashboard"
    },
    shim:{
        "bootstrap-multiselect": {
            deps: ["jquery", "bootstrap"]
        },
        "bootstrap-switch": {
            deps: ["jquery", "bootstrap"]
        },
        "sb-admin": {
            deps: ["jquery"]
        },
        "metis-menu": {
            deps: ["jquery"]
        },
        "pnotify.nonblock": {
            deps: ['pnotify']
        },
        "highcharts.core":{
            deps: ['jquery']
        },
        "highcharts.data":{
            deps: ['highcharts.core']
        },
        "highcharts.exporting":{
            deps: ['highcharts.core']
        },
        "highcharts.heatmap":{
            deps: ['highcharts.core']
        },
        "bootstrap":{
            deps: ['jquery']
        },
        "bootstrap-tooltip":{
            deps: ['bootstrap']
        },
        "renderjson":{
            exports: "renderjson"
        },
        "amcat/amcat.datatables":{
            deps: [
                'amcat/amcat',
                'datatables.plugins',
                'datatables.tabletools',
                'datatables.bootstrap',
                'jquery.cookie'
            ]
        },
        "datatables.tabletools":{
            deps: ["datatables"]
        },
        "amcat-common/dataTables.bootstrap":{
            deps: ["datatables", "bootstrap", "jquery", "datatables.tabletools"]
        },
        "datatables.plugins":{
            deps: ["datatables", "bootstrap", "jquery"]
        },
        "datatables":{
            deps: ["jquery"]
        },
        "amcat/amcat":{
            deps: ["jquery", "bootstrap"]
        }
    }
});
