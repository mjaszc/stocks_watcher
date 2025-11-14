import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";
import * as Plotly from "plotly.js-dist-min";

interface StockData {
  symbol: string;
  date: string;
  norm_20y: string;
}

interface ChartData {
  [symbol: string]: StockData[];
}

function App() {
  const [chartData, setChartData] = useState<ChartData>({});

  useEffect(() => {
    axios
      .get<ChartData>(
        "http://127.0.0.1:8000/api/v1/stocks/20y?symbols=googl.us"
      )
      .then((response) => {
        setChartData(response.data);
      })
      .catch((error) => {
        console.log(error);
      });
  }, []);

  useEffect(() => {
    if (Object.keys(chartData).length == 0) return;

    // Prepare data for Plotly
    const traces = Object.entries(chartData).map(([symbol, data]) => {
      return {
        x: data.map((item) => item.date),
        y: data.map((item) => item.norm_20y),
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
  }, [chartData]);

  return (
    <div>
      <div id="chart" style={{ width: "150%", height: "600px" }}></div>
    </div>
  );
}

export default App;
