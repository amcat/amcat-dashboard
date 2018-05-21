require(["dashboard/highcharts_demo", "sass.js/dist/sass", "bootstrap-switch"], function (highchartsDemo, Sass) {
    const sass = new Sass("/static/components/sass.js/dist/sass.worker.js");

    const container = document.getElementById("theme-demo-container");
    const style = document.getElementById("theme-demo-style");
    const colorInput = document.getElementById("id_colors");

    const colorPickerContainer = $("#color-picker");

    $(colorInput.parentElement.parentElement).hide();

    const theme_base = fetch("/static/components/highcharts/css/highcharts.scss", {credentials: "same-origin"})
        .then(x => x.text());

    sass.importer(function (request, done) {
        if (request.current === "highcharts.scss") {
            theme_base.then((content) => {
                done({content});
            });
        }
        else {
            done({error: "Only highcharts.scss is allowed as import"});
        }
    });

    function camelCaseToHumanReadable(text){
        return text.replace(/([a-z])([A-Z0-9])/g, (ab, a, b) => [a, b.toLowerCase()].join(" "))
            .replace(/^./, x => x.toUpperCase());
    }

    function debounce(fn, minInterval) {
        let t = 0;

        function wrapper(...args) {
            clearTimeout(t);
            t = setTimeout(() => fn(...args), minInterval);
        }

        return wrapper;
    }

    function update() {
        try {
            let scss = `#${container.id} { ${renderColorPickerScss(JSON.parse(colorInput.value))} }`;
            sass.compile(scss, function (result) {
                if (result.status === 0) {
                    style.innerHTML = result.text;
                }
            });
        }
        catch (e) {
            console.error(e);
        }
    }

    let throttledUpdate = debounce(update, 500);
    colorInput.addEventListener("input", () => {
        throttledUpdate();
    });

    highchartsDemo(container);

    update();

    const colorPicker = {
        inputs: [],
        defaults: {
            colors: "#7cb5ec #434348 #90ed7d #f7a35c #8085e9 #f15c80 #e4d354 #2b908f #f45b5b #91e8e1",
            backgroundColor: "#ffffff",

            neutralColor100: "#000000",
            neutralColor80: "#333333",
            neutralColor60: "#666666",
            neutralColor40: "#999999",
            neutralColor20: "#cccccc",
            neutralColor10: "#e6e6e6",
            neutralColor5: "#f2f2f2",
            neutralColor3: "#f7f7f7",

            highlightColor100: "#003399",
            highlightColor80: "#335cad",
            highlightColor60: "#6685c2",
            highlightColor20: "#ccd6eb",
            highlightColor10: "#e6ebf5"
        },

        init(container) {
            this.updateDefaults();
            for (let kv of Object.entries(this.defaults)) {
                const k = kv[0];
                let v = kv[1].split(" ");
                const row = $('<div class="row">');
                row.css('margin-top', '0.5em');
                container.append(row);

                // "camelCase10" --> "Camel case 10"
                const label = camelCaseToHumanReadable(k);

                row.append($('<div class="col-sm-3">').append($("<label>").text(label)));
                const inputgroup = $("<div class='col-sm-9'>").appendTo(row);
                let i = 0;
                for (let c of v) {
                    let input = $(`<input value="${c}" type="color" name="${k}">`);
                    this.inputs.push(input);
                    input.on('input', () => this.update());
                    inputgroup.append(input);
                    if((++i) % 5 === 0) inputgroup.append("<br>")
                }
            }
            this.update()
        },

        updateDefaults(){
            Object.assign(this.defaults, JSON.parse(colorInput.value));
        },

        update() {
            colorInput.value = JSON.stringify(this.getOptions());
            throttledUpdate();
        },

        getOptions() {
            let options = {};
            for (let input of this.inputs) {
                const k = input[0].name;
                if (options.hasOwnProperty(k)) {
                    options[k].push(input.val());
                }
                else {
                    options[k] = [input.val()];
                }
            }
            for(let k of Array.from(Object.keys(options))){
                options[k] = options[k].join(" ");
            }
            return options;
        }
    };

    colorPicker.init(colorPickerContainer);

    function renderColorPickerScss(options) {
        return `
// Colors for data series and points.
$colors: ${options.colors};

// Chart background, point stroke for markers and columns etc
$background-color: ${options.backgroundColor};

// Neutral colors, grayscale by default. The default colors are defined by mixing the
// background-color with neutral, with a weight corresponding to the number in the name.
$neutral-color-100: ${options.neutralColor100}; // Strong text.
$neutral-color-80: ${options.neutralColor80}; // Main text and some strokes.
$neutral-color-60: ${options.neutralColor60}; // Axis labels, axis title, connector fallback.
$neutral-color-40: ${options.neutralColor40}; // Credits text, export menu stroke.
$neutral-color-20: ${options.neutralColor20}; // Disabled texts, button strokes, crosshair etc.
$neutral-color-10: ${options.neutralColor10}; // Grid lines etc.
$neutral-color-5: ${options.neutralColor5}; // Minor grid lines etc.
$neutral-color-3: ${options.neutralColor3}; // Tooltip backgroud, button fills, map null points.

// Colored, shades of blue by default
$highlight-color-100: ${options.highlightColor100}; // Drilldown clickable labels, color axis max color.
$highlight-color-80: ${options.highlightColor80}; // Selection marker, menu hover, button hover, chart border, navigator series.
$highlight-color-60: ${options.highlightColor60}; // Navigator mask fill.
$highlight-color-20: ${options.highlightColor20}; // Ticks and axis line.
$highlight-color-10: ${options.highlightColor10}; // Pressed button, color axis min color.

// @import "highcharts.scss" lets us extend the default highcharts theme.
// Of course you can write your own theme from scratch.
@import "highcharts.scss"`
    }
});