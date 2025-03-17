"""Строит графики по данным из 'BMP280_pressure.csv'"""

import logging
from pathlib import Path
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, HourLocator, MinuteLocator, DateFormatter, drange
import numpy as np
import datetime as DT  # DT.datetime.now()
from collections import namedtuple
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.WARNING,
    datefmt='%H:%M:%S',  # '%Y-%m-%d %H:%M:%S'
    format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s: %(message)s',
)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.info("Starting app...")


def sleep(t=0):
    "позволяет быстро прерывать процесс по ctrl+C, не блокируя поток на полное время паузы"
    global isBreak
    t1 = time.time()
    t2 = 0.1
    while time.time() - t1 < t:
        plt.pause(t2)  # не блокирующая график пауза в отличии от time.sleep()
        if isBreak:
            log.info("exit in sleep()")
            break


# про закрытие окон: https://ru.stackoverflow.com/questions/1302494/Закрыть-интерактивное-окно-matplotlib-в-jupyter-по-кнопке-прерывания
def on_press(event):
    """collback на график"""
    log.info('you pressed', event.button, event.xdata, event.ydata)


def on_close(event):
    """collback на закрытие графика"""
    global isBreak
    log.info('Closed Figure!')
    isBreak = True
    # raise KeyboardInterrupt("Exit on close figure")
    exit()


class AbstractDataLoader(ABC):
    "Получение данных из источника"

    @abstractmethod
    def load_data(self):
        pass

    @abstractmethod
    def get_data(self):
        pass

    @abstractmethod
    def get_updated_data(self):
        pass

    @abstractmethod
    def get_last(self):
        pass


class DataCSV(AbstractDataLoader):
    SensorData = namedtuple('Meshure', ["datetimenow", "T", "P", "Piir", "Pmm", "Hum", "T_ath25"])

    def __init__(self, filename: str, n=0):
        self.filename = filename
        self.n = n
        self.data = None
        self.load_data()  # загрузить данные из файла

    def load_data(self):
        self.data = pd.DataFrame(self.load_data_from_csv(self.filename, self.n))

    def get_data(self):
        return self.data

    def get_updated_data(self):
        self.load_data()
        return self.data

    def get_last(self):
        return self.data[-1:]

    def get_last_T(self):
        return self.data[-1:]['T'].values[0]

    def load_data_from_csv(self, filename: str, n=0) -> pd.DataFrame | None:
        """Загружает историю из файла в DataFrame"""
        # формат строки в файле: f'{temperature: 2.2f} C, {pressure: 10.2f} Pa, {pressureIIR: 10.2f} Pa IIR, \
        # {pressure/cls.mmHg:3.6f} mmhg, {humidity_ATH25: 2.2f} %, {temperature_ATH25: 2.2f} C')

        try:
            df = pd.read_csv(filename, names=None, sep=";")
            # Переименовываем столбцы
            df.columns = ['datetimenow', 'T', 'P', 'Piir', 'Pmm', "Hum", "T_ath25", 'empty']

            if n == 0:
                n = len(df)

            # Преобразование типов данных
            # df['datetimenow'] = pd.to_datetime(df['datetimenow'])
            # df['T']           = df['T'].str.replace(',', '.').astype(float)

            data = []
            for _d in df[-n:].itertuples(index=False):
                # добавляем именованный кортеж
                data.append(self.SensorData(
                    # time.strptime(_d.time.strip(), '%H:%M:%S'), # '%H:%M:%S'
                    # _d.Index,
                    _d.datetimenow.strip(),
                    # float(_d.V.replace(',', '.')),
                    float(_d.T.replace(',', '.')),
                    float(_d.P.replace(',', '.')),
                    float(_d.Piir.replace(',', '.')),
                    float(_d.Pmm.replace(',', '.')),
                    float(_d.Hum.replace(',', '.')),
                    float(_d.T_ath25.replace(',', '.')),
                ))
            return data  # pd.DataFrame(data)
        except FileNotFoundError as err:
            log.error(err)
        except KeyboardInterrupt as err:
            log.info(err)


class DrowChart:
    def __init__(self, data_source: AbstractDataLoader):
        self.data_source = data_source
        # Создание окна и осей для графика
        # fig, axs = plt.subplots(nrows = 3)  # попроще конструктор
        # sharex=True - скрывает подписи на Х
        self.fig, self.axs = plt.subplots(3, 1, figsize=(10, 5), sharex=True)
        self.ax1 = self.axs[0]
        self.ax2 = self.axs[1]
        self.ax3 = self.axs[2]

        # fig.set_figheight(2)

        # Горизонтальные линии:
        # ax.vlines(2, y.min(), y.max(), color = 'r')
        # ax.hlines(5, -10, 10, color = 'b', linewidth = 3, linestyle = '--')

        # plt.axhline(y=1.2, color = 'b', linewidth = 1, linestyle='--', label='alert levels')
        # ax.hlines(y=1.2, xmin=0, xmax=n,      color = 'b', linewidth = 1, linestyle='--', label='б\\у)

        # Установка отображаемых интервалов по осям
        # ax.set_xlim(0, 4)
        # ax.set_ylim(0, 1500)

        # plt.annotate('General direction', xy = (3.4, 17)) #add annotation
        # ax.grid()  # сетка
        # Отобразить график фукнции в начальный момент времени

        # df_time = pd.DataFrame(data)['datetime'].apply(lambda x: DT.datetime.strptime(x, '%Y.%m.%d %X').astimezone()) # from timestamp

        # log.info(df_csvdata[-3:])
        self.line_p, = self.ax1.plot([], linewidth=1, linestyle='-', label='T')
        self.line_p2, = self.ax1.plot([], color='orange', linewidth=1, linestyle='-', label='T_ath25')
        self.line_d2, = self.ax3.plot([], color='g', linewidth=1, linestyle='-', marker='', label='')
        self.line_4, = self.ax2.plot([], color='r', linewidth=1, linestyle='-', marker='', label='')

        self._text = self.ax1.text(0.001, 1.1, '', transform=self.ax1.transAxes).set_text

        ax1.set_title('Temperature (T)')
        ax1.set_ylabel('T (°C)')

        # ax2.set_title('humidity, %')
        ax2.set_ylabel('Hum (%)')

        # ax3.set_title('Pressure, mmHg')
        ax3.set_ylabel('P (mm)')

        # сетка
        ax1.grid()
        ax2.grid()
        ax3.grid()

        ax1.set_xticks([])  # убрать горизонтальную ось
        ax2.set_xticks([])

        ax3.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
        fig.autofmt_xdate()

        format_time = '{:%H:%M:%S}'.format  # '{:%Y-%m-%d %H:%M:%S}' format_time(DT.datetime.now())
        # plt.legend(loc='best')

        # Повесим хук на закрытие окна графика
        # cid = fig.canvas.mpl_connect('button_press_event', on_press)
        # fig.canvas.mpl_connect('close_event', on_close)
        plt.get_current_fig_manager().canvas.mpl_connect('close_event', on_close)

        plt.tight_layout()  # для оптимального размещения элементов

        # Отобразить график динамически перерисовывая его при изменении данных
        try:
            while True:
                time_start = time.perf_counter()
                _data = data_source.get_updated_data()
                timeload = time.perf_counter() - time_start

                v = _data['T']
                current = _data['P']
                currentIIR = _data['Piir']
                currenthour = _data['Pmm']
                last = _data[-1:]
                # не использовать как last.T (транспонирует вместо получения члена)
                last_V = last['T'].values[0]

                # # способ через перерисовку всего графика, но будет мерцание
                # plt.clf() # Очистить текущую фигуру
                # # plt.fill_between(xx, 0, yy, color='lightgrey')
                # plt.plot(_price)
                # ax = pyplot.axes()
                # _text = ax.text(0.5, 0.9, '', transform=ax.transAxes).set_text
                # _text(format_time(DT.datetime.now()))
                # plt.draw()
                # plt.gcf().canvas.flush_events()

                _text(format_time(DT.datetime.now()) +
                    f', load {timeload:1.3f} с, count {len(_data)}, pause {read_sleep}c\n{last["T"].values[0]:5.2f} C, {last["T_ath25"].values[0]:5.2f} C, {last.P.values[0]:9.2f} Pa, {last.Pmm.values[0]} mmHg, {last.Hum.values[0]}%')
                # ошибка, потому что оси не настроенны
                # line.set_ydata(_price)  # Обновить данные на графике

                # Обновить данные на графике
                x = np.arange(len(_data))
                line_p.set_data(x, v)
                line_p2.set_data(x, _data['T_ath25'])
                line_4.set_data(x, _data['Hum'])

                line_d2.set_data(x, currenthour)

                # линия последнего значения. не знаю как затирать предыдущие
                # plt.axhline (y=last_price, color = 'r', linewidth = 1, linestyle='dotted')

                fig.canvas.manager.set_window_title(
                    f'{last_V:5.2f} {last.Pmm.values[0]:5.1f} [{format_time(DT.datetime.now())}]')

                # ax.set_ylim(min(val) * 0.9, int(v.max() * 1.1))
                # ax.set_xlim(0, 4)
                ax1.relim()  # update axes limits
                ax1.autoscale_view(scaley=True)

                ax2.relim()
                ax2.autoscale_view(scaley=True)

                ax3.relim()
                ax3.autoscale_view(scaley=True)

                fig.canvas.draw()
                fig.canvas.flush_events()

                sleep(read_sleep)
        except KeyboardInterrupt as err:  # Exit by Esc or ctrl+C
            log.info(err)
        finally:
            plt.close('all')  # закрыть все активные окна

        plt.ioff()  # Отключить интерактивный режим по завершению анимации
        plt.show()  # Нужно, чтобы график не закрывался после завершения анимации
            
    def update(self):
        data = self.data_source.get_updated_data()
        x = np.arange(len(data))
        self.line_p.set_data(x, data['T'])
        self.line_p2.set_data(x, data['T_ath25'])
        self.line_4.set_data(x, data['Hum'])
        self.line_d2.set_data(x, data['Pmm'])
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def sleep(t=0):
        "позволяет быстро прерывать процесс по ctrl+C, не блокируя поток на полное время паузы"
        t1 = time.time()
        t2 = 0.1
        while time.time() - t1 < t:
            plt.pause(t2)  # не блокирующая график пауза в отличии от time.sleep()
            if self.isBreak:
                log.info("exit in sleep()")
                break

    def on_press(self, event):
        """collback на график"""
        log.info('you pressed', event.button, event.xdata, event.ydata)

    def on_close(self, event):
        """collback на закрытие графика"""
        log.info('Closed Figure!')
        self.isBreak = True
        # raise KeyboardInterrupt("Exit on close figure")

    def loop(self, event):
        try:
            while True:
                self.update(x, v, _data)
                self.sleep(self.read_sleep)
        except KeyboardInterrupt as err:  # Exit by Esc or ctrl+C
            log.info(err)
        finally:
            plt.close('all')  # закрыть все активные окна
        plt.ioff()  # Отключить интерактивный режим по завершению анимации
        plt.show()  # Нужно, чтобы график не закрывался после завершения анимации
    
    def ioff(self):
        plt.ioff()  # Отключить интерактивный режим по завершению анимации
    def ion(self):
        plt.ion()  # динамический режим графика

    #===========================================================================
    def close(self):
        plt.close('all')  # закрыть все активные окна
    def show(self):
        plt.show()  # Нужно, чтобы график не закрывался после завершения анимации
    def set_title(self, title):
        self.ax1.set_title(title)
    def set_ylabel(self, ylabel):
        self.ax1.set_ylabel(ylabel)
    def grid(self):
        self.ax1.grid()
        self.ax2.grid()
        self.ax3.grid()
    def set_xticks(self):
        self.ax1.set_xticks([])  # убрать горизонтальную ось
        self.ax2.set_xticks([]) # убрать горизонтальную ось
    def set_xticks(self):
        self.ax3.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
        self.fig.autofmt_xdate()
    def set_text(self, text):
        self._text(text)
    def relim(self):
        self.ax1.relim()  # update axes limits
        self.ax1.autoscale_view(scaley=True)
        self.ax2.relim()
        self.ax2.autoscale_view(scaley=True)
        self.ax3.relim()
        self.ax3.autoscale_view(scaley=True)
    def set_window_title(self, title):
        self.fig.canvas.manager.set_window_title(title)
    def set_ylim(self, min, max):
        self.ax1.set_ylim(min, max)
    def set_xlim(self, min, max):
        self.ax1.set_xlim(min, max)
    def set_legend(self, loc='best'):
        plt.legend(loc=loc)
    def tight_layout(self):
        plt.tight_layout()  # для оптимального размещения элементов

    def connect(self, event, callback):
        plt.get_current_fig_manager().canvas.mpl_connect(event, callback)
    def pause(self, t):
        plt.pause(t)  # не блокирующая график пауза в отличии от time.sleep()
    def draw(self):
        plt.draw()  # перерисовать график
    def gcf(self):
        return plt.gcf()    # получить текущую фигуру
    def canvas(self):
        return plt.gcf().canvas    # получить текущую фигуру
    def flush_events(self):
        plt.gcf().canvas.flush_events()    # получить текущую фигуру        



def drow(data_source: AbstractDataLoader, read_sleep: int = 2) -> None:
    data_df = data_source.get_data()

    plt.ion()  # динамический режим графика
    # Создание окна и осей для графика
    # fig, axs = plt.subplots(nrows = 3)  # попроще конструктор
    # sharex=True - скрывает подписи на Х
    fig, axs = plt.subplots(3, 1, figsize=(10, 5), sharex=True)
    ax1 = axs[0]
    ax2 = axs[1]
    ax3 = axs[2]

    # fig.set_figheight(2)

    # Горизонтальные линии:
    # ax.vlines(2, y.min(), y.max(), color = 'r')
    # ax.hlines(5, -10, 10, color = 'b', linewidth = 3, linestyle = '--')

    # plt.axhline(y=1.2, color = 'b', linewidth = 1, linestyle='--', label='alert levels')
    # ax.hlines(y=1.2, xmin=0, xmax=n,      color = 'b', linewidth = 1, linestyle='--', label='б\\у)

    # Установка отображаемых интервалов по осям
    # ax.set_xlim(0, 4)
    # ax.set_ylim(0, 1500)

    # plt.annotate('General direction', xy = (3.4, 17)) #add annotation
    # ax.grid()  # сетка
    # Отобразить график фукнции в начальный момент времени

    # df_time = pd.DataFrame(data)['datetime'].apply(lambda x: DT.datetime.strptime(x, '%Y.%m.%d %X').astimezone()) # from timestamp

    # log.info(df_csvdata[-3:])
    line_p, = ax1.plot(data_df['T'], linewidth=1, linestyle='-', label='T')
    line_p2, = ax1.plot(data_df['T_ath25'], color='orange', linewidth=1, linestyle='-',
                        label='T_ath25')  # linestyle='dotted'
    line_d2, = ax3.plot(data_df['Pmm'], color='g', linewidth=1, linestyle='-', marker='', label='')
    line_4, = ax2.plot(data_df['Hum'], color='r', linewidth=1, linestyle='-', marker='', label='')
    _text = ax1.text(0.001, 1.1, '', transform=ax1.transAxes).set_text

    ax1.set_title('Temperature (T)')
    ax1.set_ylabel('T (°C)')

    # ax2.set_title('humidity, %')
    ax2.set_ylabel('Hum (%)')

    # ax3.set_title('Pressure, mmHg')
    ax3.set_ylabel('P (mm)')

    # сетка
    ax1.grid()
    ax2.grid()
    ax3.grid()

    ax1.set_xticks([])  # убрать горизонтальную ось
    ax2.set_xticks([])

    ax3.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
    fig.autofmt_xdate()

    format_time = '{:%H:%M:%S}'.format  # '{:%Y-%m-%d %H:%M:%S}' format_time(DT.datetime.now())
    # plt.legend(loc='best')

    # Повесим хук на закрытие окна графика
    # cid = fig.canvas.mpl_connect('button_press_event', on_press)
    # fig.canvas.mpl_connect('close_event', on_close)
    plt.get_current_fig_manager().canvas.mpl_connect('close_event', on_close)

    plt.tight_layout()  # для оптимального размещения элементов

    # Отобразить график динамически перерисовывая его при изменении данных
    try:
        while True:
            time_start = time.perf_counter()
            _data = data_source.get_updated_data()
            timeload = time.perf_counter() - time_start

            v = _data['T']
            current = _data['P']
            currentIIR = _data['Piir']
            currenthour = _data['Pmm']
            last = _data[-1:]
            # не использовать как last.T (транспонирует вместо получения члена)
            last_V = last['T'].values[0]

            # # способ через перерисовку всего графика, но будет мерцание
            # plt.clf() # Очистить текущую фигуру
            # # plt.fill_between(xx, 0, yy, color='lightgrey')
            # plt.plot(_price)
            # ax = pyplot.axes()
            # _text = ax.text(0.5, 0.9, '', transform=ax.transAxes).set_text
            # _text(format_time(DT.datetime.now()))
            # plt.draw()
            # plt.gcf().canvas.flush_events()

            _text(format_time(DT.datetime.now()) +
                  f', load {timeload:1.3f} с, count {len(_data)}, pause {read_sleep}c\n{last["T"].values[0]:5.2f} C, {last["T_ath25"].values[0]:5.2f} C, {last.P.values[0]:9.2f} Pa, {last.Pmm.values[0]} mmHg, {last.Hum.values[0]}%')
            # ошибка, потому что оси не настроенны
            # line.set_ydata(_price)  # Обновить данные на графике

            # Обновить данные на графике
            x = np.arange(len(_data))
            line_p.set_data(x, v)
            line_p2.set_data(x, _data['T_ath25'])
            line_4.set_data(x, _data['Hum'])

            line_d2.set_data(x, currenthour)

            # линия последнего значения. не знаю как затирать предыдущие
            # plt.axhline (y=last_price, color = 'r', linewidth = 1, linestyle='dotted')

            fig.canvas.manager.set_window_title(
                f'{last_V:5.2f} {last.Pmm.values[0]:5.1f} [{format_time(DT.datetime.now())}]')

            # ax.set_ylim(min(val) * 0.9, int(v.max() * 1.1))
            # ax.set_xlim(0, 4)
            ax1.relim()  # update axes limits
            ax1.autoscale_view(scaley=True)

            ax2.relim()
            ax2.autoscale_view(scaley=True)

            ax3.relim()
            ax3.autoscale_view(scaley=True)

            fig.canvas.draw()
            fig.canvas.flush_events()

            sleep(read_sleep)
    except KeyboardInterrupt as err:  # Exit by Esc or ctrl+C
        log.info(err)
    finally:
        plt.close('all')  # закрыть все активные окна

    plt.ioff()  # Отключить интерактивный режим по завершению анимации
    plt.show()  # Нужно, чтобы график не закрывался после завершения анимации


BASE_PATH = Path(__file__).parent


def main():
    global isBreak
    isBreak = False
    # количество n последних элементов из истории для отображения. 
    # n = 0 - использовать все данные
    N_last = 30 * 60 * 12
    read_sleep = 2  # период опроса файла в секундах, либо вешать файловой системы на изменение файла

    filename = BASE_PATH.joinpath('BMP280_pressure.csv')
    filename_demo = BASE_PATH.joinpath('BMP280_pressure_demo.csv')

    if not filename.exists():
        log.warning(f"{filename} not found. Using '{filename_demo}'")
        if not filename_demo.exists():
            log.error(f"{filename_demo} not found")
            exit(0)
        filename = filename_demo

    data_source = DataCSV(filename, N_last)

    if (data_source.get_data() is None):
        log.error("No data")
        exit(0)

    # chart = DrowChart(data_source)
    drow(data_source, read_sleep)

if __name__ == "__main__":
    main()
