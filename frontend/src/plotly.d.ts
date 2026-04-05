declare module 'react-plotly.js/factory' {
  import type { ComponentType } from 'react';
  import type Plotly from 'plotly.js-dist-min';

  interface PlotParams {
    data: Plotly.Data[];
    layout?: Partial<Plotly.Layout>;
    config?: Partial<Plotly.Config>;
    style?: React.CSSProperties;
    useResizeHandler?: boolean;
  }

  export default function createPlotlyComponent(
    plotly: typeof Plotly,
  ): ComponentType<PlotParams>;
}

declare module 'plotly.js-dist-min' {
  import Plotly from 'plotly.js';
  export = Plotly;
}
