# ARIMA dynamic graph, for financial markets and other data

Dynamic ARIMA plot in a sliding window.

In this code, data obtained from yfinance is used to display on the chart.
Closing prices are used. In this dataframe, this is column number three. You can substitute your own data of this kind in df. All graphics are done in PyQt5.

The bottommost slider is used to set the scale (this is how many candles should be in the window). The slider above the bottom one is for scrolling the chart.

ARIMA is launched by pressing a button. Pressing again deletes the ARIMA series and the vertical bar.

ARIMA is drawn if there are available values for training and prediction. If you notice that the data is not updating, then you need to scroll the graph so that there is enough data.

After changing the settings, you need to move the cursor and after that the calculation will be with the new settings.

The following libraries are required to work: 

PyQt5, PyQtChart, statsmodels, yfinance, numpy

P.S. An additional series(dt_line_serie) with datetime indexes has been added so that there are no gaps on the chart when there is no trading.

![Visually, everything looks like this](https://github.com/quant12345/Dynamic-ARIMA/blob/main/arima.gif)




