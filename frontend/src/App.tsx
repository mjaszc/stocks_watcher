import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";
import * as Plotly from "plotly.js-dist-min";
import { SelectButton } from "primereact/selectbutton";

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
  const [stocks, setStocks] = useState(["amzn.us", "aapl.us", "googl.us"]);
  const [chartData, setChartData] = useState<ChartData>({});

  const timeHorizons = [
    { label: "1 Months", value: "1mo" },
    { label: "3 Months", value: "3mo" },
    { label: "6 Months", value: "6mo" },
    { label: "1 Year", value: "1y" },
    { label: "5 Years", value: "5y" },
    { label: "20 Years", value: "20y" },
  ];

  useEffect(() => {
    const baseUrl = "http://127.0.0.1:8000/api/v1/stocks";
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
      },
      yaxis: {
        title: {
          text: "Normalized Value",
        },
      },
      hovermode: "closest" as const,
    };

    Plotly.newPlot("chart", traces, layout);
  }, [chartData, timeframe]);

  return (
    <>
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
