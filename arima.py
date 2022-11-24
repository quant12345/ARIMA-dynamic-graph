from PyQt5 import QtCore, QtWidgets, QtChart
from PyQt5.QtWidgets import QSpinBox, QLabel, QFormLayout
from PyQt5.QtCore import *
from PyQt5.QtChart import *
import statsmodels.api as sm
import yfinance as yf
import math
import numpy as np
import datetime

df = yf.download('IBM', start='2000-01-01', end='2022-04-30')
date = df.index
x = len(df)
x_ = x - 1
#In this case, the closing price is used. This is column number three.
column_index = 3

qt = [None] * x

for i in range(0, x):
    qt[i] = QDateTime(date[i]).toMSecsSinceEpoch()


class ARIMAchart(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ARIMAchart, self).__init__(parent)
        self.setMouseTracking(True)

        self.resize(self.window().widget2.size())
        #Create a vertical stripe
        self._band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Line, self)
        self._band.setGeometry(350, 0, 2, 550)
        self._band.show()
        self.show()

    def mouseMoveEvent(self, event):
        a = QtCore.QPoint(event.pos().x(), self._band.maximumHeight())
        b = QtCore.QPoint(event.pos().x() + 1, 2)
        self._band.setGeometry(QtCore.QRect(a, b).normalized())

        self.resize(self.window().size())
        self._band.update()

        chart_view = self.window().splitter.widget(0)
        chart = chart_view.chart()
        s = chart.series()

        viewPos = chart_view.mapFrom(self.window().widget2, event.pos())
        scenePos = chart_view.mapToScene(viewPos)
        chartItemPos = chart.mapFromScene(scenePos)
        #Get the value on the x-axis at the position of the cursor
        x = int(round(chart.mapToValue(chartItemPos).x()))

        def my_func(line_serie):#Set the limits for the axes.
            xmin = self.window().imin
            xmax = self.window().imax
            minY = np.amin(df.iloc[int(xmin): int(xmax) + 1, column_index])
            maxY = np.amax(df.iloc[int(xmin): int(xmax) + 1, column_index])
            chart.axisX(line_serie).setRange(xmin, xmax)
            chart.axisY(line_serie).setRange(minY, maxY)

        def arima():#Get ARIMA
            mod = sm.tsa.arima.ARIMA(df.iloc[x - self.window().tr.value():x+1, column_index].values, order=(
                self.window().p.value(), self.window().d.value(), self.window().q.value()))
            res = mod.fit()
            fc = res.forecast(self.window().te.value())

            return fc

        #If ARIMA is not created and there is available data for calculation, then we create a forecast
        if len(s) <= 2 and x > self.window().tr.value():
            line_serie = QtChart.QLineSeries()
            line_serie.setName('ARIMA')
            fc = arima()
            aaa = []
            for i in range(0, self.window().te.value()):
                aaa.append(QtCore.QPointF(int(x + i), fc[i]))

            chart.addSeries(line_serie)

            axisX = QValueAxis()
            axisX.setTickCount(5)
            axisX.setLabelFormat("%d")
            chart.addAxis(axisX, Qt.AlignBottom)
            line_serie.attachAxis(axisX)

            axisY = QValueAxis()
            chart.addAxis(axisY, Qt.AlignLeft)
            line_serie.attachAxis(axisY)

            chart.axisX(line_serie).setVisible(False)
            chart.axisY(line_serie).setVisible(False)
            my_func(line_serie)
        else:
            """Check if there is available data for training and prediction.
               If there is enough data, update ARIMA
            """
            if (x + self.window().te.value()) <= x_ and x > self.window().tr.value():
                for serie in s:
                    if serie.name() == 'ARIMA':
                        fc = arima()
                        aaa = []
                        for i in range(0, self.window().te.value()):
                            aaa.append(QtCore.QPointF(int(x + i), fc[i]))

                        my_func(serie)
                        serie.replace(aaa)



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.step = 0
        self._chart_view = QtChart.QChartView()

        self.widget2 = QtWidgets.QWidget()
        self.layV = QtWidgets.QVBoxLayout(self.widget2)
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.layV.addWidget(self.splitter)

        hbox = QtWidgets.QHBoxLayout()

        ar = QFormLayout()
        differenced = QFormLayout()
        ma = QFormLayout()
        train = QFormLayout()
        test = QFormLayout()
        """
        Here are windows of values ARIMA(p, d, q) and number of elements to train(self.tr)
         and predictions (self.te)
        """
        P = QLabel('P')
        D = QLabel('D')
        Q = QLabel('Q')
        Tr = QLabel('quantity for training')
        Te = QLabel('quantity for forecast')

        self.p = QSpinBox()
        self.d = QSpinBox()
        self.q = QSpinBox()
        self.tr = QSpinBox()
        self.te = QSpinBox()

        for w in (self.tr, self.te):
            w.setMaximum(100000)
        # Default values
        self.p.setValue(2)
        self.d.setValue(0)
        self.q.setValue(1)
        self.tr.setValue(120)
        self.te.setValue(15)
        """ 
        Button that creates ARIMA. Pressing again deletes the ARIMA series and hides the vertical bar
        """
        self.button = QtWidgets.QPushButton('Show ARIMA')

        ar.addRow(P, self.p)
        differenced.addRow(D, self.d)
        ma.addRow(Q, self.q)
        train.addRow(Tr, self.tr)
        test.addRow(Te, self.te)
        hbox.addLayout(ar, 0)
        hbox.addLayout(differenced, 0)
        hbox.addLayout(ma, 0)
        hbox.addLayout(train, 0)
        hbox.addLayout(test, 0)
        hbox.addWidget(self.button)

        self.button.clicked.connect(self.handleButton)

        """ 
        self.scrollbar scroll chart
        self.slider sets the chart scale
        """
        self.scrollbar = QtWidgets.QScrollBar(
            QtCore.Qt.Horizontal,
            sliderMoved=self.SliderMoved,
            pageStep=self.step,
        )
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal,
                                        sliderMoved=self.ZoomSlider)

        self.scrollbar.setRange(0, x_)
        aaa = int(x / 5)
        self.slider.setRange(1, aaa)
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        lay = QtWidgets.QVBoxLayout(central_widget)
        lay.insertLayout(0, hbox)
        for w in (self._chart_view, self.widget2, self.scrollbar, self.slider):
            lay.addWidget(w)

        """ 
        Two series are created: one with integer indices, the other with datetime indices.
        This must be done to remove gaps on the x-axis on weekends and holidays. The line self.dt_line_serie is hidden,
        and its axisX is shown. The line self.int_line_serie is shown and the axisX is hidden.
        """
        self._chart = QtChart.QChart()
        self.dt_line_serie = QtChart.QLineSeries()
        self.int_line_serie = QtChart.QLineSeries()
        self.int_line_serie.setColor(Qt.darkGreen)

        for i in range(0, len(df)):
            self.dt_line_serie.append(qt[i], df.iloc[i, column_index])
            self.int_line_serie.append(float(i), df.iloc[i, column_index])

        self._chart.addSeries(self.int_line_serie)
        self._chart.addSeries(self.dt_line_serie)
        self._chart.legend().hide()

        self._chart_view.setChart(self._chart)

        axisX = QValueAxis()
        axisX.setTickCount(5)
        axisX.setLabelFormat("%d")
        self._chart.addAxis(axisX, Qt.AlignBottom)
        self.int_line_serie.attachAxis(axisX)

        axisX = QDateTimeAxis()
        axisX.setTickCount(5)
        axisX.setFormat("yyyy-MM-dd")
        self._chart.addAxis(axisX, Qt.AlignBottom)
        self.dt_line_serie.attachAxis(axisX)

        axisY = QValueAxis()
        self._chart.addAxis(axisY, Qt.AlignLeft)
        self.dt_line_serie.attachAxis(axisY)
        self.int_line_serie.attachAxis(axisY)

        self.dt_line_serie.setVisible(False)
        self._chart.axisX(self.int_line_serie).setVisible(False)

        self.splitter.addWidget(self._chart_view)

        self.band = ARIMAchart(self.widget2)#class to create ARIMA and vertical bar
        self.band.setVisible(False)

        self.imax = x_
        self.imin = x_ - self.tr.value()
        self.step = self.imax - self.imin

        self.slider.setValue(int(x_ / self.step))
        self.scrollbar.setValue(x_ - self.tr.value())
        self.SliderMoved(self.scrollbar.value())
        self.adjust_axes(x_ - self.tr.value(), x_)

    # Setting the limits of the x, y axes (scaling)
    def adjust_axes(self, value_min, value_max):
        if value_min >= 0 and value_max > 0 and value_max > value_min:
            self._chart.axisX(self.int_line_serie).setRange(value_min, value_max)

            t1 = datetime.datetime.combine(date[value_min], datetime.time())
            t2 = datetime.datetime.combine(date[value_max], datetime.time())
            self._chart.axisX(self.dt_line_serie).setRange(t1, t2)

            ymin = np.amin(df.iloc[int(value_min): int(value_max) + 1, column_index])
            ymax = np.amax(df.iloc[int(value_min): int(value_max) + 1, column_index])
            self._chart.axisY(self.dt_line_serie).setRange(ymin, ymax)
            self._chart.axisY(self.int_line_serie).setRange(ymin, ymax)

    # graph scrolling
    def SliderMoved(self, value):
        value2 = value + self.step
        if value2 >= x_:
            value2 = x_
        value1 = value2 - self.step
        self.imax = int(value2)
        self.imin = int(value1)
        self.adjust_axes(math.floor(self.imin), math.ceil(self.imax))

    # setting window step for scale
    def ZoomSlider(self, value):
        self.step = x_ / value
        self.SliderMoved(x_ - self.step)

    def handleButton(self):
        if not self.band.isVisible():
            self.band.show()
            self.button.setText('Hide ARIMA')
        else:
            self.band.hide()
            self.button.setText('Show ARIMA')
            for serie in self._chart_view.chart().series():
                if serie.name() == 'ARIMA':
                    serie.clear()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
