import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";
import Plotly from "plotly.js-dist-min";
import { SelectButton } from "primereact/selectbutton";
import { MultiSelect } from "primereact/multiselect";

import "primereact/resources/themes/lara-dark-teal/theme.css";
import "primereact/resources/primereact.min.css";
import "primeicons/primeicons.css";

const DEFAULT_STOCKS = [
  "NVDA.US",
  "AAPL.US",
  "MSFT.US",
  "AMZN.US",
  "GOOGL.US",
  "META.US",
  "AVGO.US",
  "TSLA.US",
];

interface StockData {
  symbol: string;
  date: string;
  norm_1mo?: string;
  norm_3mo?: string;
  norm_6mo?: string;
  norm_1y?: string;
  norm_5y?: string;
}

interface ChartData {
  [symbol: string]: StockData[];
}

interface Anomaly {
  date_index: number;
  price: number;
  return_pct: number;
  z_score: number;
}

interface AnomalyData {
  [symbol: string]: Anomaly[];
}

const timeframeToNormField: Record<string, keyof StockData> = {
  "1mo": "norm_1mo",
  "3mo": "norm_3mo",
  "6mo": "norm_6mo",
  "1y": "norm_1y",
  "5y": "norm_5y",
};

function App() {
  const [timeframe, setTimeframe] = useState("6mo");
  const [stocks, setStocks] = useState<string[]>(() => {
    const savedStocks = localStorage.getItem("user_selected_stocks");
    return savedStocks ? JSON.parse(savedStocks) : DEFAULT_STOCKS;
  });

  const [stockOptions, setStockOptions] = useState([]);
  const [chartData, setChartData] = useState<ChartData>({});
  const [anomalyData, setAnomalyData] = useState<AnomalyData>({});

  const timeHorizons = [
    { label: "1 Months", value: "1mo" },
    { label: "3 Months", value: "3mo" },
    { label: "6 Months", value: "6mo" },
    { label: "1 Year", value: "1y" },
    { label: "5 Years", value: "5y" },
  ];

  const stockSelectOptions = stockOptions.map((symbol) => ({
    label: symbol,
    value: symbol,
  }));

  useEffect(() => {
    localStorage.setItem("user_selected_stocks", JSON.stringify(stocks));
  }, [stocks]);

  // Retrieving stock symbols
  useEffect(() => {
    const url = "/api/v1/stocks/symbols";
    axios
      .get(url)
      .then((response) => {
        setStockOptions(response.data);
      })
      .catch((error) => {
        console.log(error);
      });
  }, []);

  useEffect(() => {
    if (stocks.length === 0) return;

    const stocksParam = stocks.join(",");

    // Request for Line Chart Data
    const chartUrl = `/api/v1/stocks/${timeframe}?symbols=${stocksParam}`;
    const chartReq = axios.get<ChartData>(chartUrl);

    // Request for Anomaly Data
    const anomalyUrl = `/api/v1/stocks/anomalies/${timeframe}?symbols=${stocksParam}`;
    const anomalyReq = axios.get<AnomalyData>(anomalyUrl);

    // Fetch both in parallel
    Promise.all([chartReq, anomalyReq])
      .then(([chartRes, anomalyRes]) => {
        setChartData(chartRes.data);
        setAnomalyData(anomalyRes.data);
      })
      .catch((error) => {
        console.log("Error fetching data:", error);
      });
  }, [timeframe, stocks]);

  useEffect(() => {
    if (Object.keys(chartData).length === 0) return;

    const normField = timeframeToNormField[timeframe];

    // Prepare data for Plotly
    const traces = Object.entries(chartData).flatMap(([symbol, data]) => {
      // Line Trace
      const dates = data.map((item) => item.date);
      const prices = data.map((item) => item[normField] as string);

      const lineTrace = {
        x: dates,
        y: prices,
        type: "scatter" as const,
        mode: "lines" as const,
        name: symbol,
        line: { width: 2 },
        legendgroup: symbol,
      };

      // Create the Anomaly Marker Tracing (if anomalies exist)
      const stockAnomalies = anomalyData[symbol];

      if (stockAnomalies && stockAnomalies.length > 0) {
        const anomalyTrace = {
          // Map anomaly back to the correct date string
          x: stockAnomalies.map((a) => dates[a.date_index]),
          y: stockAnomalies.map((a) => a.price),
          mode: "markers" as const,
          type: "scatter" as const,
          name: `${symbol} Alerts`,
          legendgroup: symbol,
          showlegend: false,

          marker: {
            symbol: "diamond",
            size: 10,
            color: "#fbbf24",
            line: { color: "white", width: 1 },
          },

          hoverinfo: "text" as const,
          text: stockAnomalies.map(
            (a) =>
              `<b>${symbol} Event</b><br>` +
              `Return: ${a.return_pct}%<br>` +
              `Z-Score: ${a.z_score}`,
          ),
        };

        return [lineTrace, anomalyTrace];
      }

      return [lineTrace];
    });

    const layout = {
      xaxis: {
        title: { text: "Date" },
        type: "date" as const,
        gridcolor: "rgba(255, 255, 255, 0.1)",
        color: "rgba(255, 255, 255, 0.87)",
      },
      yaxis: {
        title: { text: "Normalized Value" },
        gridcolor: "rgba(255, 255, 255, 0.1)",
        color: "rgba(255, 255, 255, 0.87)",
      },
      hovermode: "closest" as const,
      paper_bgcolor: "#1f2937",
      plot_bgcolor: "#1f2937",
      font: {
        color: "rgba(255, 255, 255, 0.87)",
        family:
          'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      },
    };

    const config = {
      displayModeBar: false,
      displaylogo: false,
      responsive: true,
    };

    Plotly.newPlot("chart", traces, layout, config);
  }, [chartData, anomalyData, timeframe]);

  return (
    <>
      <MultiSelect
        value={stocks}
        onChange={(e) => {
          if (e.value.length > 0) {
            setStocks(e.value);
          }
        }}
        options={stockSelectOptions}
        optionLabel="label"
        optionValue="value"
        display="chip"
        placeholder="Select Stocks"
        maxSelectedLabels={5}
        className="w-full md:w-20rem"
        panelStyle={{ maxHeight: "300px" }}
        filter
      />

      <SelectButton
        value={timeframe}
        onChange={(e) => setTimeframe(e.value)}
        options={timeHorizons}
      />
      <div>
        <div id="chart" style={{ width: "100%", height: "600px" }}></div>
      </div>
    </>
  );
}

export default App;
