/**
 * charts.js — Renderização e configuração dos gráficos ApexCharts para telemetria industrial.
 */

const industrialChartTheme = {
    mode: "dark",
    palette: "palette1",
    monochrome: {
        enabled: false,
    },
};

const defaultChartOptions = {
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
    theme: industrialChartTheme,
    stroke: {
        curve: "smooth",
        width: 2.5,
    },
    grid: {
        borderColor: "#2a3348",
        strokeDashArray: 3,
        xaxis: { lines: { show: true } },
        yaxis: { lines: { show: true } },
    },
    xaxis: {
        type: "datetime",
        labels: {
            style: { colors: "#8892a8", fontSize: "11px", fontFamily: "Inter" },
            datetimeUTC: false,
        },
        axisBorder: { color: "#2a3348" },
        axisTicks: { color: "#2a3348" },
    },
    tooltip: {
        theme: "dark",
        x: { format: "dd/MM/yyyy HH:mm" },
    },
};

/**
 * Cria ou atualiza um gráfico de telemetria com linhas de limites operacionais.
 */
function createTelemetryChart(elementId, config = {}) {
    const {
        title = "",
        seriesName = "Leitura",
        dataPoints = [], // [{ x: timestampMs, y: valor, min, max }]
        unit = "",
        limiteAtencao = null,
        limiteCritico = null,
        color = "#3b82f6",
    } = config;

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

    const options = {
        ...defaultChartOptions,
        title: {
            text: title,
            align: "left",
            style: { color: "#ffffff", fontSize: "14px", fontWeight: 600, fontFamily: "Inter" },
        },
        colors: [color],
        series,
        annotations,
        yaxis: {
            title: {
                text: unit ? `Valor (${unit})` : "Valor",
                style: { color: "#8892a8", fontSize: "12px", fontFamily: "Inter" },
            },
            labels: {
                style: { colors: "#8892a8", fontSize: "11px", fontFamily: "JetBrains Mono" },
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
    const options = {
        ...defaultChartOptions,
        colors: ["#3b82f6", "#10b981", "#f59e0b", "#ec4899"],
        series: seriesList,
        yaxis: {
            title: {
                text: unit ? `Valor (${unit})` : "Valor",
                style: { color: "#8892a8", fontSize: "12px", fontFamily: "Inter" },
            },
            labels: {
                style: { colors: "#8892a8", fontSize: "11px", fontFamily: "JetBrains Mono" },
                formatter: (val) => (val !== null && val !== undefined ? val.toFixed(2) : ""),
            },
        },
        legend: {
            position: "top",
            horizontalAlign: "right",
            labels: { colors: "#e4e8f1" },
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
    const options = {
        chart: {
            type: "donut",
            height: 220,
            background: "transparent",
        },
        theme: industrialChartTheme,
        series: [goodCount, uncertainCount, badCount],
        labels: ["Good (0)", "Uncertain (0x40000000)", "Bad (0x80000000)"],
        colors: ["#10b981", "#f59e0b", "#ef4444"],
        stroke: { show: false },
        dataLabels: { enabled: false },
        legend: {
            position: "bottom",
            labels: { colors: "#8892a8" },
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
                            color: "#8892a8",
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
