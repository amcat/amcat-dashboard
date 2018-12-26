require([
    "jquery",
    "dashboard/highcharts_demo"
], function (
    $,
    highchartsDemo
) {


    const previewContainer = document.getElementById("theme-demo-container");
    const previewStyle = document.getElementById("theme-demo-style");
    const themeForm = document.getElementById("theme-form");
    const colorInput = document.getElementById("id_colors");
    const yAxisLineWidthInput = document.getElementById("id_y_axis_line_width");
    const yAxisHasLineColorInput = document.getElementById("id_y_axis_has_line_color");
    const yLabelHasLineColorInput = document.getElementById("id_y_label_has_line_color");
    const colorPickerContainer = $("#color-picker");

    let demoChart = null;

    function camelCaseToHumanReadable(text) {
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

    function updatePreview() {
        demoChart.update(Object.assign({}, demoChart.options, colorPicker.getOptions()))
    }

    const throttledUpdate = debounce(updatePreview, 500);

    const colorPicker = {
        inputs: [],
        defaults: {
            colors: "#7cb5ec #434348 #90ed7d #f7a35c #8085e9 #f15c80 #e4d354 #2b908f #f45b5b #91e8e1"
        },

        init(container) {
            container = $(container);
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
                    if ((++i) % 5 === 0) inputgroup.append("<br>")
                }
            }
            this.update()
        },

        updateDefaults() {
            Object.assign(this.defaults, {colors: colorInput.value});
        },

        update() {
            colorInput.value = this.getOptions().colors.join(' ');
            throttledUpdate();
        },

        /**
         * The highcharts options for this setting
         */
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
            if (options.colors) {
                console.log( yAxisHasLineColorInput.checked );
                options.yAxis = [
                    {
                        lineWidth: yAxisLineWidthInput.value,
                        lineColor: yAxisHasLineColorInput.checked ? options.colors[0] : "#666666",
                        title: {style: {color: yLabelHasLineColorInput.checked ? options.colors[0] : "#666666"}}
                    },
                    {
                        lineWidth: yAxisLineWidthInput.value,
                        lineColor: yAxisHasLineColorInput.checked ? options.colors[1] : "#666666",
                        title: {style: {color: yLabelHasLineColorInput.checked ? options.colors[1] : "#666666"}}
                    }];
            }
            return options;
        },

    };


    function initThemeEditor() {
        $(colorInput.parentElement.parentElement).hide();

        themeForm.addEventListener("input", () => {
            throttledUpdate();
        });


        demoChart = highchartsDemo(previewContainer);

        updatePreview();
        colorPicker.init(colorPickerContainer);
    }

    initThemeEditor();
});