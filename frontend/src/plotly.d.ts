declare module 'react-plotly.js' {
  import { Component } from 'react';
  import type Plotly from 'plotly.js-dist-min';

  interface PlotParams {
    data: Plotly.Data[];
    layout?: Partial<Plotly.Layout>;
    config?: Partial<Plotly.Config>;
    style?: React.CSSProperties;
    useResizeHandler?: boolean;
    onInitialized?: (figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> }, graphDiv: HTMLElement) => void;
    onUpdate?: (figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> }, graphDiv: HTMLElement) => void;
  }

  export default class Plot extends Component<PlotParams> {}
}

declare module 'plotly.js-dist-min' {
  import type Plotly from 'plotly.js';
  export = Plotly;
}
