"""
Создаем файлы .csv из сырых данных, которые хранятся в хэше программы SBPro
В рассмотрение берем тайм фреймы: 5 минут, 1 час, 1 день, 1 неделя

Следующие свойства можно добавить позже:
[] Объем сделок внутри спреда.
    Если глянуть на общий объем и сумму покупок и продаж, то можно заметить, что не всегда эти значения совпадают.
    Это значит, что какие-то сделки прошли внутри сперда. Например, между ценой в 60.23 и 60.24 есть цена 60.235,
    но у нас градация сотая часть, и эта сделка не отобразилась в buy или sell, но отобразилась в общем объеме
Для тайм фрема 1 день:
    [] Какой день недели. ПН-ВС
    [] День перед праздником и день после праздника
Для тайм фрема 1 час:
    [] Какой час. 0-23
Для тайм фрема 5 мин:
    [] Какая пятиминутка. 1-12
"""
import datetime
from typing import List, Literal
import os
import time


# ----------------------------------------------------------------------------------------------------------------------
# region Константы

TF = Literal["5m", "1h", "1d", "1w"]
# индексы
I_FUTURES = 1
I_HIGH = 2
I_LOW = 3
I_OPEN = 4
I_CLOSE = 5
# имена столбцов
NAMES_COLS = [
    "Time",                             # 0         17:00:00
    "Futures",                          # 1         03-26
    "HIGH",                             # 2         6071
    "LOW",                              # 3         6043
    "OPEN",                             # 4         6062
    "CLOSE",                            # 5         6066
    "VOLUME",                           # 6         296
    "BUY",                              # 7         124
    "SELL",                             # 8         163
    "ORDERS",                           # 9         221
]
for ii in range(1, 5):
    NAMES_COLS.append(f"VQ{ii}")        # 10-13     Объем в каждой четверти
for ii in range(1, 5):
    NAMES_COLS.append(f"BQ{ii}")        # 14-17     Покупки в каждой четверти
for ii in range(1, 5):
    NAMES_COLS.append(f"SQ{ii}")        # 18-21     Продажи в каждой четверти
for ii in range(1, 5):
    NAMES_COLS.append(f"MAX_VQ{ii}")    # 22-25     Максимальный объем контрактов в четверти в 1 тике
for ii in range(1, 5):
    NAMES_COLS.append(f"MAX_BQ{ii}")    # 26-29     Максимальная покупка в четверти в 1 тике
for ii in range(1, 5):
    NAMES_COLS.append(f"MAX_SQ{ii}")    # 30-33     Максимальная продажа в четверти в 1 тике

NAMES_COLS.append("GAP")                # 34        Был ли разрыв в цене:
#                                                   0 - не был;
#                                                   1 - ценовой (вышли какие-то новости, после выходных или праздников);
#                                                   2 - межконтрактный
NAMES_COLS.append("GAP_BARS")           # 35        Как быстро закрылся. 0 - не закрылся за 100 баров,
#                                                   иначе 1 - (кол-во баров - 1) / 100
#                                                   Но что делать, если нет у нас 100 баров впереди и gap не закрылся?
#                                                   Тоже ставим 0
# endregion

# ----------------------------------------------------------------------------------------------------------------------
# region Необходимые ф-ии


def my_timer(func):
    """
    Засекаем время работы ф-ии func с обязательным параметром s_str
    """
    def wrapper(s_str, *args, **kwargs):
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] START:  {func.__name__}({s_str})")
        f_time = time.perf_counter()
        func(s_str, *args, **kwargs)
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FINISH: {func.__name__}({s_str}) | "
              f"{(time.perf_counter() - f_time):.2f} сек")
        return func
    return wrapper


def files_from_dir(dirpath: str, be_sort: bool = True) -> List[str]:
    """
    Список всех файлов в каталоге и в подкаталогах
    """
    res = []
    for dir_path, dir_names, file_names in os.walk(dirpath):
        res.extend([os.path.join(dir_path, x) for x in file_names])
    if be_sort:
        res.sort()
    return res


def bar_info_base(lst: list) -> list:
    """
    Базовые данные бара. Цену ставим в центах
    Используем round вместо int, т.к. если это не сделать, то вместо 60.71 получим 7070
    """
    # 170000 -> 17:00:00
    s_time = lst[0][:2] + ":" + lst[0][2:4] + ":" + lst[0][4:]
    return [s_time,                         # 0:    Time:         17:00:00
            lst[2],                         # 1:    Контракт:     03-26
            round(float(lst[3]) * 100),     # 2:    HIGH:         60.71 -> 6071
            round(float(lst[4]) * 100),     # 3:    LOW:          60.43 -> 6043
            round(float(lst[5]) * 100),     # 4:    OPEN:         60.62 -> 6062
            round(float(lst[6]) * 100),     # 5:    CLOSE:        60.66 -> 6066
            lst[7],                         # 6:    VOLUME:       296
            lst[10],                        # 7:    BUY:          124
            lst[11],                        # 8:    SELL:         163
            ]


def ticks_info(lst_ticks: list) -> List[list]:
    """
    Список данных на каждом уровне бара. Цену ставим в центах
    """
    lst_levels = []
    for st in lst_ticks:
        lst = st.split(":")
        lst_levels.append([
            round(float(lst[0]) * 100),     # 0:     Цена:        60.62 -> 6062
            int(lst[1]),                    # 1:     VOLUME:      1611
            int(lst[5]),                    # 2:     BUY:         636
            int(lst[6]),                    # 3:     SELL:        963
            int(lst[8]),                    # 4:     ORDERS:      1139
        ])
    # отсортируем в порядке возростания значения тика
    return sorted(lst_levels, key=lambda x: x[0])


def calc_index_lst(high: int, low: int) -> List[list[int]]:
    """
    Вычисляем границы [start, end] для каждой четверти в зависимости от кол-ва тиков баре.
    Это разница между max и min бара в тиках, а не величина len от списка тиков, т.к. на уровне могло и не быть сделок
    Q1 - максимальные значения, Q4 - минимальные. Как бар делим, где свеху маx, снизу min.
    """
    n, p = divmod(high - low + 1, 4)

    # если бар меньше 4 тиков
    if n == 0:
        if p == 1:
            return [[high, high]] * 4
        if p == 2:
            return [[high, high]] * 2 + [[low, low]] * 2
        if p == 3:
            return [[high, high]] + [[high - 1, high - 1]] * 2 + [[low, low]]

    # для удобства сперва делим от меньшего к большему
    res = [x for i in range(0, 4) for x in [i * n, (i + 1) * n - 1]]
    for k in range(0, p):
        for i in range(k * 2 + 3, 8):
            res[i] = res[i] + 1
    # возврщаем в обратном порядке - от большего к меньшему
    return [[res[i + 1] + low, res[i] + low] for i in range(6, -2, -2)]


def calc_info_quart_split(high: int, low: int, lst_levels: List[list], res_list: list):
    """
    Разбиваем бар на 4 части и в каждой вычисляем:
        0:  VQ1-VQ4:            Объем
        1:  BQ1-BQ4:            Покупки
        2:  SQ1-SQ4:            Продажи
        3:  MAX_VQ1-MAX_VQ4:    Максимальный объем контрактов в четверти в 1 тике
        4:  MAX_BQ1-MAX_BQ4:    Максимальная покупка в четверти в 1 тике
        5:  MAX_SQ1-MAX_SQ4:    Максимальная продажа в четверти в 1 тике
    """
    # вычисляем индексы [start, end] для каждой четверти
    q_indx = calc_index_lst(high, low)
    # массив дополнительных данных для каждой четверти
    q_data = {i: [0] * 6 for i in range(4)}

    for lst in lst_levels:
        for i in range(4):
            if q_indx[i][0] >= lst[0] >= q_indx[i][1]:  # i-ая четверть
                q_data[i][0] += lst[1]
                q_data[i][1] += lst[2]
                q_data[i][2] += lst[3]
                q_data[i][3] = max(q_data[i][3], lst[1])
                q_data[i][4] = max(q_data[i][4], lst[2])
                q_data[i][5] = max(q_data[i][5], lst[3])

    # добавляем новые данные
    for j in range(6):
        for i in range(4):
            res_list.append(q_data[i][j])


def info_from_file(tf: TF, filename: str) -> List[list] or str:
    """
    Извлекаем из filename данные
    filename такого вида path/2024-02-25.locchache
    """
    line_i = 0
    try:
        date_s = os.path.basename(filename).split(".")[0]  # 2024-02-25
        res = []
        with open(filename, 'rt', encoding="utf-8") as f:
            for line_i, line in enumerate(f):
                # сперва разделим на [данные о баре] и [данные о каждом значении в баре]
                st_bar, st_lst = line.split(":0*")

                # Базовые данные бара
                lst_bar = bar_info_base(st_bar.split(":"))
                if tf in ["5m", "1h"]:
                    lst_bar[0] = date_s + ' ' + lst_bar[0]
                else:  # 1d и 1w
                    lst_bar[0] = date_s

                # Список данных на каждом уровне бара
                lst_levels = ticks_info(st_lst.split("|"))

                # 9:  ORDERS = Общее кол-во заявок = сумма заявок на каждом уровне бара
                lst_bar.append(sum([x[4] for x in lst_levels]))

                # делим бар на 4 части, для каждой части получаем данные, добавляем новые св-ва бара
                calc_info_quart_split(lst_bar[I_HIGH], lst_bar[I_LOW], lst_levels, lst_bar)

                res.append(lst_bar)

        return res
    except Exception as e:
        return f"[info_from_file][{filename}][{line_i}]: except: {repr(e)}"


def calc_gap_bars(bars: List[list]):
    """
    Добавляем данные о GAP в бары
    """
    for i, bar in enumerate(bars):
        if (i + 1 >= len(bars)) or (bar[I_CLOSE] == bars[i + 1][I_OPEN]):
            bar.extend([0, 0])  # последний бар или нет гэпа
        else:
            # Узнаем, это был межконтрактный гэп или ценовой
            if bar[I_FUTURES] == bars[i + 1][I_FUTURES]:
                x = 1  # ценовой
            else:
                x = 2  # межконтрактный
            k = 1
            while (i + k < len(bars)) and (k <= 100):  # не выйти за рамки и не более 100 баров
                if bars[i + k][I_LOW] <= bar[I_CLOSE] <= bars[i + k][I_HIGH]:
                    bar.extend([x, round(1 - (k - 1) / 100, 2)])  # закрыли гэп с коэффициентом
                    break
                k += 1
            else:
                bar.extend([x, 0])  # не закрыли гэп


@my_timer
def create_bars_dataset(tf: TF, path_dir: str, add_path: str = ""):
    """
    Создаем датасет в .csv
    """
    work_step = ''
    try:
        # список файлов отсортирован, ранняя дата в начале
        work_step = "files_list"
        files_list = files_from_dir(path_dir)
        file_start = os.path.basename(files_list[0]).split(".")[0]
        file_end = os.path.basename(files_list[-1]).split(".")[0]
        res = []
        work_step = "info_from_file"
        for file_s in files_list:
            lst = info_from_file(tf, file_s)
            if isinstance(lst, str):  # ошибка работы
                print(f"Ошибка работы: {lst}")
                break
            res.extend(lst)
        work_step = "calc_gap_bars"
        calc_gap_bars(res)

        res_s = ",".join(NAMES_COLS) + "\n"
        res_s += "\n".join([",".join(map(str, x)) for x in res])

        # сохраняем файл
        with open(f"{add_path}{file_start}-{file_end}_{tf}.csv", "w", encoding="UTF-8") as f:
            f.write(res_s)
    except Exception as e:
        return f"[create_bars_dataset][{work_step}]: except: {repr(e)}"

# endregion

# ----------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
    dir_1w = r"/content/data_source/604800/0.01/Central Standard Time"
    dir_1d = r"/content/data_source/86400/0.01/Central Standard Time"
    dir_1h = r"/content/data_source/3600/0.01/Central Standard Time"
    dir_5m = r"/content/data_source/300/0.01/Central Standard Time/0.0"
    new_path = r"/content/drive/MyDrive/Colab_Notebooks/AI_2025/M14/data/"
    create_bars_dataset("1w", dir_1w, new_path)
    create_bars_dataset("1d", dir_1d, new_path)
    create_bars_dataset("1h", dir_1h, new_path)
    create_bars_dataset("5m", dir_5m, new_path)

# end
