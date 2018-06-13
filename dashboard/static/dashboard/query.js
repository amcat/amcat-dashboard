define([
    "jquery",
    "query/renderers",
    "query/utils/i18n"
], function ($, renderers, i18n) {

    const _ = i18n.gettext;

    const STRINGS = {
        actions: _("Actions"),
        viewOnAmcat: _("View on AmCAT"),
        refresh: _("Refresh")
    };

    const template = query => `
<div class="panel-heading">
    <div class="pull-right">
        <div class="btn-group">
            <button type="button" class="btn btn-default btn-xs dropdown-toggle" data-toggle="dropdown">
                ${STRINGS.actions}
                <span class="caret"></span>
            </button>
            <ul class="dropdown-menu pull-right" role="menu">
                <li>
                    <a href="${query.clear_cache_url}">
                        <i class="fa fa-refresh fa-fw"></i> ${STRINGS.refresh}
                    </a>
                </li>
                <li>
                    <a href="${query.amcat_url}" target="_blank">
                        <span class="fa fa-external-link fa-fw"></span>
                        ${STRINGS.viewOnAmcat}
                    </a>
                </li>
            </ul>
        </div>
    </div>
    <i class="query-icon fa fa-bar-chart-o fa-fw"></i> <span class="query-name">${query.name}</span>
</div>
<div class="query-canvas panel-body"></div>
`;


    function get(url) {
        return fetch(url, {
            credentials: "same-origin",
            cache: "no-cache",
        });
    }

    function getJSON(url) {
        return get(url).then(r => r.json());
    }

    class QueryRenderer {
        constructor(container) {
            this.container = $(container);
            this.themeArgs = this.container.data('theme');
            this.url = this.container.data('saved-query-src');
        }

        async onQueryFetched(query) {
            const result = await QueryRenderer.fetchQueryResult(query);

            renderers[query.output_type](query.amcat_parameters, this.container.find('.query-canvas'), result);

            // apply theme args if a theme is selected.
            if (this.themeArgs === null) {
                return;
            }
            console.log(this);
            this.container.find('[data-highcharts-chart]').each((i, el) => {
                el = $(el);
                const chart = el.highcharts();
                if (chart instanceof Highcharts.Chart) {
                    chart.update(Highcharts.merge(chart.options, this.themeArgs));
                }
            });
        }

        async render() {
            const query = await getJSON(this.url);
            this.container.html(template(query));
            await this.onQueryFetched(query);
            this.container.find(".query-name").text(query.amcat_name);
        }

        static async fetchQueryResult(query) {
            const response = await get(query.result_url);
            return query.output_type.indexOf('json') >= 0 ? await response.json() : await response.text();
        }
    }

    function renderQuery(container) {
        let renderer = new QueryRenderer(container);
        return renderer.render();
    }

    function renderQueries(containers) {
        return Promise.all($(containers).toArray().map(container => renderQuery(container)))
    }

    return {
        renderQuery,
        renderQueries
    };
});