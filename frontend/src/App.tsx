import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";
import Plotly from "plotly.js-dist-min";
import { SelectButton } from "primereact/selectbutton";
import { MultiSelect } from "primereact/multiselect";

import "primereact/resources/themes/lara-dark-teal/theme.css";
import "primereact/resources/primereact.min.css";
import "primeicons/primeicons.css";

interface StockData {
  symbol: string;
  date: string;
  norm_1mo?: string;
  norm_3mo?: string;
  norm_6mo?: string;
  norm_1y?: string;
  norm_5y?: string;
  norm_20y?: string;
}

interface ChartData {
  [symbol: string]: StockData[];
}

// Map selected timeframe accordingly to norm price field from api
const timeframeToNormField: Record<string, keyof StockData> = {
  "1mo": "norm_1mo",
  "3mo": "norm_3mo",
  "6mo": "norm_6mo",
  "1y": "norm_1y",
  "5y": "norm_5y",
  "20y": "norm_20y",
};

function App() {
  const [timeframe, setTimeframe] = useState("6mo");
  // State for currently selected stocks
  const [stocks, setStocks] = useState(["AMZN.US", "AAPL.US", "GOOGL.US"]);
  // State for stock options for multiselect
  const [stockOptions, setStockOptions] = useState([]);
  const [chartData, setChartData] = useState<ChartData>({});

  // For filtering timeframe inside api endpoint
  const timeHorizons = [
    { label: "1 Months", value: "1mo" },
    { label: "3 Months", value: "3mo" },
    { label: "6 Months", value: "6mo" },
    { label: "1 Year", value: "1y" },
    { label: "5 Years", value: "5y" },
    { label: "20 Years", value: "20y" },
  ];

  const stockSelectOptions = stockOptions.map((symbol) => ({
    label: symbol,
    value: symbol,
  }));

  // Retrieving stock symbols from database
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

  // Calling URL for chart generation
  useEffect(() => {
    const baseUrl = "/api/v1/stocks";
    const stocksParam = stocks.join(",");
    const url = `${baseUrl}/${timeframe}?symbols=${stocksParam}`;

    axios
      .get<ChartData>(url)
      .then((response) => {
        setChartData(response.data);
      })
      .catch((error) => {
        console.log(error);
      });
  }, [timeframe, stocks]);

  // Generating chart
  useEffect(() => {
    if (Object.keys(chartData).length == 0) return;

    const normField = timeframeToNormField[timeframe];

    // Prepare data for Plotly
    const traces = Object.entries(chartData).map(([symbol, data]) => {
      return {
        x: data.map((item) => item.date),
        y: data.map((item) => item[normField] as string),
        type: "scatter" as const,
        mode: "lines" as const,
        name: symbol,
        line: { width: 2 },
      };
    });

    const layout = {
      xaxis: {
        title: {
          text: "Date",
        },
        type: "date" as const,
        gridcolor: "rgba(255, 255, 255, 0.1)",
        color: "rgba(255, 255, 255, 0.87)",
      },
      yaxis: {
        title: {
          text: "Normalized Value",
        },
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
  }, [chartData, timeframe]);

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
