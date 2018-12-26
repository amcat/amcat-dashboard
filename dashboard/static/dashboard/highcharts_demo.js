define(["highcharts.core"], function(Highcharts){
    const bus = document.createElement('div');
    const interval = null;

    const DEFAULT_OPTS = {
        title: {
            text: 'Example'
        },
        subtitle: {
            text: 'Example subtitle'
        },
        yAxis: [{
            title: {
                text: 'Y Axis 1',
            }
        },{
            title: {
                text: 'Y Axis 2',
            },
            opposite: true,
        }],
        legend: {
            layout: 'horizontal',
            align: 'right',
        },

        plotOptions: {
            series: {
                label: {
                    connectorAllowed: false
                },
                pointStart: 2010
            }
        },

        series: [{
            name: 'Installation',
            data: [43934, 52503, 57177, 69658, 97031, 119931, 137133, 154175]
        }, {
            name: 'Manufacturing',
            data: [-249, -240, -90, 8, 64, 152, 381, 404],
            yAxis: 1
        }, {
            name: 'Sales & Distribution',
            data: [11744, 17722, 16005, 19771, 20185, 24377, 32147, 39387]
        }, {
            name: 'Project Development',
            data: [null, null, 7988, 12169, 15112, 22452, 34400, 34227]
        }, {
            name: 'Other',
            data: [12908, 5948, 8105, 11248, 8989, 11816, 18274, 18111]
        }],

    };

    function highchartsDemo(container, ...options){
        const highchartsOptions = Highcharts.merge(DEFAULT_OPTS, ...options);
        let chart = Highcharts.chart(container, highchartsOptions);
        return chart;
    }

    return highchartsDemo;
});