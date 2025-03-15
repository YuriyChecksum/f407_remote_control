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

logging.basicConfig(
    # level=logging.DEBUG,
    # filename='test_logging.log', filemode='w',
    # datefmt='%Y-%m-%d %H:%M:%S',
    datefmt='%H:%M:%S',
    format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s: %(message)s',
)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.info("Starting app...")

def load_data_from_csv(filename: str, n=0):
    """Загружает историю из файла в DataFrame"""
    # формат строки в файле: f'{temperature: 2.2f} C, {pressure: 10.2f} Pa, {pressureIIR: 10.2f} Pa IIR, \
    # {pressure/cls.mmHg:3.6f} mmhg, {humidity_ATH25: 2.2f} %, {temperature_ATH25: 2.2f} C')

    try:
        df = pd.read_csv(filename, names=None, sep=";")
        # Переименовываем столбцы
        df.columns = ['datetimenow', 'T', 'P', 'Piir', 'Pmm', "Hum", "T_ath25", 'empty']

        if n==0:
          n = len(df)
        
        # Преобразование типов данных
        # df['datetimenow'] = pd.to_datetime(df['datetimenow'])
        # df['T']           = df['T'].str.replace(',', '.').astype(float)

        data = []
        for _d in df[-n:].itertuples(index=False):
          # добавляем именованный кортеж
          data.append(Meshure(
            #time.strptime(_d.time.strip(), '%H:%M:%S'), # '%H:%M:%S'
            #_d.Index,
            _d.datetimenow.strip(),
            #float(_d.V.replace(',', '.')),
            float(_d.T.replace(',', '.')),
            float(_d.P.replace(',', '.')),
            float(_d.Piir.replace(',', '.')),
            float(_d.Pmm.replace(',', '.')),
            float(_d.Hum.replace(',', '.')),
            float(_d.T_ath25.replace(',', '.')),
            ))
        return pd.DataFrame(data)
    except FileNotFoundError as err:
        log.error(err)
    except KeyboardInterrupt as err:
        log.info(err)

def sleep(t=0):
    "позволяет быстро прерывать процесс по ctrl+C, не блокируя поток на полное время паузы"
    global isBreak
    t1 = time.time()
    t2 = 0.1
    while time.time() - t1 < t:
        # time.sleep(t2)
        plt.pause(t2) # не блокирующая график пауза в отличии от time.sleep()
        if isBreak:
            log.info("exit in sleep()")
            break

def on_press(event):
    """collback на график"""
    log.info('you pressed', event.button, event.xdata, event.ydata)

def on_close(event):
    """collback на закрытие графика"""
    global isBreak
    log.info('Closed Figure!')
    isBreak = True
    raise KeyboardInterrupt("Exit on close figure", "KeyboardInterrupt для прерывания loop")

if __name__ == "__main__":
    n = 30*60*12    # n=0 - использовать все | n элементов из истории и на графике
    _sleep = 2
    isBreak = False

    filename = Path('BMP280_pressure.csv')

    Meshure = namedtuple('Meshure', ["datetimenow", "T", "P", "Piir", "Pmm", "Hum", "T_ath25"])

    df_csvdata = load_data_from_csv(filename, n)

    if (df_csvdata is None):
        log.error("csv data is None")
        exit(0)

    plt.ion() # динамический режим графика
    #fig, axs = plt.subplots(nrows = 3)  # Создание окна и осей для графика
    fig, axs = plt.subplots(3, 1, figsize=(10, 5), sharex=True)  # Создание окна и осей для графика  sharex=True скрывает подписи на Х
    ax = axs[0]
    ax1 = ax
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
    line_p, = ax.plot(df_csvdata['T'], linewidth = 1, linestyle='-', label='T')
    line_p2, = ax.plot(df_csvdata['T_ath25'], color = 'orange', linewidth = 1, linestyle='-', label='T_ath25') # linestyle='dotted'
    line_d2, = ax3.plot(df_csvdata['Pmm'], color = 'g', linewidth = 1, linestyle='-', marker='', label='')
    line_4, = ax2.plot(df_csvdata['Hum'], color = 'r', linewidth = 1, linestyle='-', marker='', label='')
    _text = ax.text(0.001, 1.1, '', transform=ax.transAxes).set_text

    ax.set_title('Temperature (T)')
    ax.set_ylabel('T (°C)')

    #ax2.set_title('humidity, %')
    ax2.set_ylabel('Hum (%)')

    #ax3.set_title('Pressure, mmHg')
    ax3.set_ylabel('P (mm)')

    # сетка
    ax.grid()
    ax2.grid()
    ax3.grid()

    ax1.set_xticks([]) # убрать горизонтальную ось
    ax2.set_xticks([])

    ax3.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
    fig.autofmt_xdate()

    format_time = '{:%H:%M:%S}'.format  # '{:%Y-%m-%d %H:%M:%S}' format_time(DT.datetime.now())
    #plt.legend(loc='best')

    # Повесим хук на закрытие окна графика
    # cid = fig.canvas.mpl_connect('button_press_event', on_press)
    # fig.canvas.mpl_connect('close_event', on_close)
    plt.get_current_fig_manager().canvas.mpl_connect('close_event', on_close)

    plt.tight_layout() # для оптимального размещения элементов

    try:
      while True:  # for i in range(10):
        time_start = time.perf_counter()
        _data = load_data_from_csv(filename, n)
        timeload = time.perf_counter() - time_start

        v           = _data['T']
        current     = _data['P']
        currentIIR  = _data['Piir']
        currenthour = _data['Pmm']
        last = _data[-1:]
        # не использовать как last.T (транспонирует вместо получения члена)
        last_V = last['T'].values[0]

        # # через перерисовку всего графика
        # plt.clf() # Очистить текущую фигуру
        # # plt.fill_between(xx, 0, yy, color='lightgrey')
        # plt.plot(_price)
        # ax = pyplot.axes()
        # _text = ax.text(0.5, 0.9, '', transform=ax.transAxes).set_text
        # _text(format_time(DT.datetime.now()))
        # plt.draw()
        # plt.gcf().canvas.flush_events()

        _text(format_time(DT.datetime.now()) +
            f', load {timeload:1.3f} с, count {len(_data)}, pause {_sleep}c\n{last["T"].values[0]:5.2f} C, {last["T_ath25"].values[0]:5.2f} C, {last.P.values[0]:9.2f} Pa, {last.Pmm.values[0]} mmHg, {last.Hum.values[0]}%')
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

        fig.canvas.manager.set_window_title(f'{last_V:5.2f} {last.Pmm.values[0]:5.1f} [{format_time(DT.datetime.now())}]')

        # ax.set_ylim(min(val) * 0.9, int(v.max() * 1.1))
        # ax.set_xlim(0, 4)
        ax.relim()  # update axes limits
        ax.autoscale_view(scaley=True)

        ax2.relim()
        ax2.autoscale_view(scaley=True)

        ax3.relim()
        ax3.autoscale_view(scaley=True)

        fig.canvas.draw()
        fig.canvas.flush_events()

        sleep(_sleep)
    except KeyboardInterrupt as err: # Exit by Esc or ctrl+C
        log.info(err)
        plt.close('all') #   закрыть все активные окна
    
    plt.ioff()  # Отключить интерактивный режим по завершению анимации
    plt.show()  # Нужно, чтобы график не закрывался после завершения анимации

    # про закрытие окон: https://ru.stackoverflow.com/questions/1302494/Закрыть-интерактивное-окно-matplotlib-в-jupyter-по-кнопке-прерывания