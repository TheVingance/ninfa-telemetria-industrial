/**
 * charts.js — Renderização e configuração dos gráficos ApexCharts para telemetria industrial.
 * Suporta alternância dinâmica entre Tema Escuro e Tema Claro.
 */

function getChartThemeConfig() {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    return {
        mode: isLight ? "light" : "dark",
        borderColor: isLight ? "#cbd5e1" : "#2a3348",
        textColor: isLight ? "#475569" : "#8892a8",
        titleColor: isLight ? "#0f172a" : "#ffffff",
        tooltipTheme: isLight ? "light" : "dark",
    };
}

function buildDefaultChartOptions() {
    const tc = getChartThemeConfig();
    return {
        chart: {
            type: "line",
            height: 380,
            background: "transparent",
            toolbar: {
                show: true,
                tools: {
                    download: true,
                    selection: true,
                    zoom: true,
                    zoomin: true,
                    zoomout: true,
                    pan: true,
                    reset: true,
                },
            },
            animations: {
                enabled: true,
                easing: "easeinout",
                speed: 400,
            },
        },
        theme: {
            mode: tc.mode,
            monochrome: { enabled: false },
        },
        stroke: {
            curve: "smooth",
            width: 2.5,
        },
        grid: {
            borderColor: tc.borderColor,
            strokeDashArray: 3,
            xaxis: { lines: { show: true } },
            yaxis: { lines: { show: true } },
        },
        xaxis: {
            type: "datetime",
            labels: {
                style: { colors: tc.textColor, fontSize: "11px", fontFamily: "Inter" },
                datetimeUTC: false,
            },
            axisBorder: { color: tc.borderColor },
            axisTicks: { color: tc.borderColor },
        },
        tooltip: {
            theme: tc.tooltipTheme,
            x: { format: "dd/MM/yyyy HH:mm" },
        },
    };
}

/**
 * Cria ou atualiza um gráfico de telemetria com linhas de limites operacionais.
 */
function createTelemetryChart(elementId, config = {}) {
    const {
        title = "",
        seriesName = "Leitura",
        dataPoints = [],
        unit = "",
        limiteAtencao = null,
        limiteCritico = null,
        color = "#3b82f6",
    } = config;

    const tc = getChartThemeConfig();
    const annotations = { yaxis: [] };

    if (limiteAtencao !== null) {
        annotations.yaxis.push({
            y: limiteAtencao,
            borderColor: "#f59e0b",
            strokeDashArray: 4,
            label: {
                borderColor: "#f59e0b",
                style: { color: "#ffffff", background: "#b45309", fontSize: "11px" },
                text: `Atenção: ${limiteAtencao} ${unit}`,
            },
        });
    }

    if (limiteCritico !== null) {
        annotations.yaxis.push({
            y: limiteCritico,
            borderColor: "#ef4444",
            strokeDashArray: 4,
            label: {
                borderColor: "#ef4444",
                style: { color: "#ffffff", background: "#b91c1c", fontSize: "11px" },
                text: `Crítico: ${limiteCritico} ${unit}`,
            },
        });
    }

    const series = [
        {
            name: seriesName,
            data: dataPoints.map((p) => ({ x: p.x, y: p.y })),
        },
    ];

    const baseOptions = buildDefaultChartOptions();
    const options = {
        ...baseOptions,
        title: {
            text: title,
            align: "left",
            style: { color: tc.titleColor, fontSize: "14px", fontWeight: 600, fontFamily: "Inter" },
        },
        colors: [color],
        series,
        annotations,
        yaxis: {
            title: {
                text: unit ? `Valor (${unit})` : "Valor",
                style: { color: tc.textColor, fontSize: "12px", fontFamily: "Inter" },
            },
            labels: {
                style: { colors: tc.textColor, fontSize: "11px", fontFamily: "JetBrains Mono" },
                formatter: (val) => (val !== null && val !== undefined ? val.toFixed(2) : ""),
            },
        },
    };

    const chartEl = document.getElementById(elementId);
    if (!chartEl) return null;
    chartEl.innerHTML = "";
    const chart = new ApexCharts(chartEl, options);
    chart.render();
    return chart;
}

/**
 * Gráfico comparativo multi-série (sobreposição de grandezas ou máquinas).
 */
function createComparisonChart(elementId, seriesList = [], unit = "") {
    const tc = getChartThemeConfig();
    const baseOptions = buildDefaultChartOptions();

    const options = {
        ...baseOptions,
        colors: ["#3b82f6", "#10b981", "#f59e0b", "#ec4899"],
        series: seriesList,
        yaxis: {
            title: {
                text: unit ? `Valor (${unit})` : "Valor",
                style: { color: tc.textColor, fontSize: "12px", fontFamily: "Inter" },
            },
            labels: {
                style: { colors: tc.textColor, fontSize: "11px", fontFamily: "JetBrains Mono" },
                formatter: (val) => (val !== null && val !== undefined ? val.toFixed(2) : ""),
            },
        },
        legend: {
            position: "top",
            horizontalAlign: "right",
            labels: { colors: tc.textColor },
        },
    };

    const chartEl = document.getElementById(elementId);
    if (!chartEl) return null;
    chartEl.innerHTML = "";
    const chart = new ApexCharts(chartEl, options);
    chart.render();
    return chart;
}

/**
 * Gráfico de rosca para integridade da qualidade do dado OPC UA.
 */
function createQualityDonut(elementId, goodCount, uncertainCount, badCount) {
    const tc = getChartThemeConfig();
    const options = {
        chart: {
            type: "donut",
            height: 220,
            background: "transparent",
        },
        theme: {
            mode: tc.mode,
        },
        series: [goodCount, uncertainCount, badCount],
        labels: ["Good (0)", "Uncertain (0x40000000)", "Bad (0x80000000)"],
        colors: ["#10b981", "#f59e0b", "#ef4444"],
        stroke: { show: false },
        dataLabels: { enabled: false },
        legend: {
            position: "bottom",
            labels: { colors: tc.textColor },
        },
        plotOptions: {
            pie: {
                donut: {
                    size: "70%",
                    labels: {
                        show: true,
                        total: {
                            show: true,
                            label: "Total Amostras",
                            color: tc.textColor,
                            formatter: (w) => w.globals.seriesTotals.reduce((a, b) => a + b, 0),
                        },
                    },
                },
            },
        },
    };

    const chartEl = document.getElementById(elementId);
    if (!chartEl) return null;
    chartEl.innerHTML = "";
    const chart = new ApexCharts(chartEl, options);
    chart.render();
    return chart;
}
