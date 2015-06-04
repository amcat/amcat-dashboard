requirejs.config({
    "baseUrl": "/static/components",
    "paths": {
        "query": "../query",
        "jquery": "jquery/dist/jquery",
        "papaparse": "papaparse/papaparse",
        "highlight": "highlight/build/highlight.pack",
        "highcharts.core": "highcharts/highcharts",
        "highcharts.data": "highcharts/modules/data",
        "highcharts.exporting": "highcharts/modules/exporting",
        "highcharts.heatmap": "highcharts/modules/heatmap",
        "bootstrap": "bootstrap/dist/js/bootstrap",
        "bootstrap-multiselect": "bootstrap-multiselect/dist/js/bootstrap-multiselect",
        "bootstrap-tooltip": "bootstrap/js/tooltip",
        "bootstrap-datepicker": "bootstrap-datepicker/dist/js/bootstrap-datepicker",
        "moment": "moment/moment",
        "renderjson": "renderjson/renderjson",
        "datatables": "datatables/media/js/jquery.dataTables",
        "datatables.tabletools": "datatables/extensions/TableTools/js/dataTables.tableTools",
        "jshashset": "jshashtable/hashset",
        "jshashtable": "jshashtable/hashtable",
        "query/utils/articlemodal": "../query/utils/mock",
        "jquery.cookie": "jquery-cookie/jquery.cookie",
        "metis-menu": "metisMenu/dist/metisMenu",
        "sb-admin": "startbootstrap-sb-admin-2/dist/js/sb-admin-2",
        "pnotify": "pnotify/pnotify.core",
        "pnotify.nonblock": "pnotify/pnotify.nonblock"
    },
    shim:{
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
        "datatables.bootstrap":{
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
