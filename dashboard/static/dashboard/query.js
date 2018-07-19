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
                    <form class="hidden" method="post" action="${query.clear_cache_url}" id="clear-cache-${query.id}">
                        ${CSRF_TOKEN_INPUT}
                    </form>
                    <a data-submit="#clear-cache-${query.id}">
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
    <i class="query-icon fa fa-bar-chart-o fa-fw"></i> <span class="query-name"></span>
</div>
<div class="query-canvas panel-body"></div>
`;

    function sleep(milliseconds) {
        return new Promise((resolve) => setTimeout(() => resolve(), milliseconds))
    }

    function get(url, options) {
        return fetch(url, {
            credentials: "same-origin",
            cache: "no-cache",
        });
    }

    function getJSON(url) {
        return get(url).then(r => r.json());
    }

    function isObj(obj){
        return obj !== null && typeof obj === "object";
    }

    class QueryRenderer {
        constructor(container, options) {
            this.filterForm = options.filterForm;
            this.container = $(container);
            this.themeArgs = this.container.data('theme');
            this.customizeArgs = this.container.data('customize');
            this.url = this.container.data('saved-query-src');
        }

        async onQueryFetched(query) {
            const result = await this.fetchQueryResult(query);
            this._preRender(query);
            renderers[query.output_type](query.amcat_parameters, this.container.find('.query-canvas'), result);
            this._postRender(query);
        }

        _preRender(query){
            // hacky: amcat-query relies on certain form elements being present during rendering.
            // this temporarily adds those form elements to the DOM.
            this.magic_div = $('<div>').hide().appendTo(document.body);
            if (isObj(query.amcat_options) && isObj(query.amcat_options.form)) {
                this.magic_div.append(Object.values(query.amcat_options.form));
                console.debug("Magic div:", this.magic_div)
            }
        }

        _postRender(){
            this.magic_div.remove();
            this.magic_div = $(null);

            // apply theme args if a theme is selected.
            this.container.find('[data-highcharts-chart]').each((i, el) => {
                el = $(el);
                const chart = el.highcharts();
                if (chart instanceof Highcharts.Chart) {
                    const newOptions = Highcharts.merge({}, chart.options, this.themeArgs, this.customizeArgs);
                    console.debug("Override options: ", newOptions);
                    chart.update(newOptions);
                }
            });
        }


        async render() {
            const query = await getJSON(this.url);
            this.container.html(template(query));
            this.bindEvents(this.container);
            await this.onQueryFetched(query);
            this.container.find(".query-name").text(query.amcat_name);
        }

        bindEvents(container) {
            container.find('[data-submit]').each((i, el) => {
                el = $(el);
                const tgt = container.find(el.data('submit'));
                el.click(() => tgt.submit());
            })
        }

        async fetchQueryResult(query) {
            let q = null;
            if(this.filterForm !== undefined){
                q = this.filterForm.elements['q'].value
            }
            const querystr = q ? `?q=${encodeURIComponent(q)}` : '';

            const response = await get(`${query.result_url}${querystr}`);
            if(query.output_type.indexOf('json') >= 0){
                const data = await response.json();
                if(data.status === "pending"){
                    await sleep(500);
                    return await this.fetchQueryResult(query);
                }
                return data;
            }
            return await response.text();
        }
    }

    function renderQuery(container, options) {
        let renderer = new QueryRenderer(container, options);
        return renderer.render();
    }

    function renderQueries(containers, options) {
        return Promise.all($(containers).toArray().map(container => renderQuery(container, options)))
    }

    return {
        renderQuery,
        renderQueries
    };
});