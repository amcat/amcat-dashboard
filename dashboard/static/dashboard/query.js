define([
    "jquery",
    "query/renderers",
    "query/utils/i18n",
    "highcharts.core"
], function ($, renderers, i18n, Highcharts) {

    const _ = i18n.gettext;

    const STRINGS = {
        actions: _("Actions"),
        viewOnAmcat: _("View on AmCAT"),
        refresh: _("Refresh"),
        download: _("Download as CSV")
    };

    const template = (query, title, page_link) => {

    if (page_link !== undefined) {
        title_element = `<a href=${page_link} class="query-name">${title}</a>`
        heading_attr = `onclick="window.location='${page_link}'"  style="cursor: pointer;"`
    } else {
        title_element = `<span class="query-name">${title}</span>`
        heading_attr = ""
    }
    return `
<div class="query-heading panel-heading" ${heading_attr}>
    <h4 class="query-title">${title_element}</h4>
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
            <li class="if-downloadable">
                <a data-init-download-url="${query.init_download_url}" data-target="#download-dialog">
                    <i class="fa fa-download fa-fw"></i> ${STRINGS.download}
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
<div class="query-canvas panel-body"></div>
`;}

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
            this.title = this.container.data('title');
            this.page_link = this.container.data('pagelink');
            this.customizeArgs = this.container.data('customize');
            this.url = this.container.data('saved-query-src');
        }

        async onQueryFetched(query) {
            const result = await this.fetchQueryResult(query);
            this._preRender(query);
            const [output_type, meaning] = query.output_type.split(';');
            const parameters = Object.assign({}, query.amcat_parameters);
            const extraOptions = {valueRendererOptions: {neverShowId: true}}; // TODO: configurable options
            renderers[output_type](parameters, this.container.find('.query-canvas'), result, extraOptions);
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

            this._applyCustomization();
            this._renderedSummaryToListing();
        }
        _applyCustomization(){
            this.container.find('[data-highcharts-chart]').each((i, el) => {
                el = $(el);
                const chart = el.highcharts();
                if (chart instanceof Highcharts.Chart) {
                    const newOptions = Highcharts.merge({}, chart.options, this.themeArgs, this.customizeArgs,
                        this.chartExportingOptions);
                    console.debug("Theme: ", this.themeArgs);
                    console.debug("Customize: ", this.customizeArgs);
                    console.debug("Override options: ", newOptions);
                    chart.update(newOptions);
                }
            });
        }

        _renderedSummaryToListing() {
            let article_ul = this.container.find('ul.articles');
            let aggregations = this.container.find('[data-highcharts-chart]');
            if (article_ul.length === 0 || aggregations.length > 0) {
                return; // not a summary, or a summary with aggregations.
            }

            const lis = article_ul.children();
            const listing = $('<div class="query-listing list-group">');
            listing.append(lis);
            lis.addClass("list-group-item");
            this.container.find('.query-canvas').remove();
            this.container.append(listing);

            listing.find('a').each((i,a) => {
                const url = new URL(a.href);
                a.href = a.href.replace(url.origin, DASHBOARD_SYSTEM.hostname);
            });
        }

        async render() {
            const query = await getJSON(this.url);
            this.container.html(template(query, this.title, this.page_link));
            this.bindEvents(this.container, query);
            await this.onQueryFetched(query);
            this.container.find(".if-downloadable").toggle(query.is_downloadable);
        }

        bindEvents(container, query) {
            container.find('[data-submit]').each((i, el) => {
                el = $(el);
                const tgt = container.find(el.data('submit'));
                el.click(() => tgt.submit());
            });
            container.find('[data-init-download-url]').click(e => {
                const self = $(e.target);
                const tgt = $(self.data('target'));
                const progressBar = tgt.find('.download-progress');
                const statusText = tgt.find('.download-status');
                progressBar.show();
                progressBar.removeClass("progress-failed");
                progressBar[0].removeAttribute("value");
                statusText.text("Getting ready...");
                tgt.modal();
                fetch(self.data("init-download-url")).then(async response => {
                    const json = await response.json();

                    tgt.attr("data-poll-url", json.poll_uri);

                    while(true){
                        const response = await fetch(json.poll_uri).then(r => r.json());
                        const result = response['results'][0];
                        if(result.status === "SUCCESS"){
                            progressBar.hide();
                            statusText
                                .html(`<a class="btn btn-success" href="${response.result_url}">Download</a>`);
                            break;
                        }
                        else if(result.status === "INPROGRESS"){
                            progressBar[0].value = result.progress.completed;
                        }
                        else if(result.status === "FAILURE"){
                            statusText.html(`Download failed. ${result.error.exc_message}`);
                            break;
                        }
                        await sleep(500);
                    }
                }).catch(e => {
                    statusText.text(`Download failed: ${e}`);
                    progressBar[0].value = Math.max(progressBar[0].value, 20);
                    progressBar.addClass('progress-failed');
                });
            });
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

        get chartExportingOptions(){
            return {
                exporting: {chartOptions: {title: {text: this.title}}}
            }
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
