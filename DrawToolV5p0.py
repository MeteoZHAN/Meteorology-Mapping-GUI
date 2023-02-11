# -*- coding: utf-8 -*-
"""
@Features:
@Author: L.F. Zhan
@Date：2023/2/11
"""

import tkinter as tk
from tkinter import filedialog, ttk
import tkinter.messagebox as tm
from tkinter.colorchooser import *
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import matplotlib.cm as cm
import matplotlib.colors as colors
from PIL import Image, ImageTk
import cartopy.io.shapereader as shpreader
from scipy.interpolate import Rbf
from shapely.ops import unary_union
import shapefile
import pandas as pd
from shapely.geometry import Polygon
import numpy as np
import cartopy.crs as ccrs
from io import BytesIO
import win32clipboard

# from pykrige import OrdinaryKriging

# 设置中文显示字体
plt.rcParams['font.sans-serif'] = ['FangSong']  # 用来正常显示中文字符
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

window = tk.Tk()
window.title('江西省气象空间插值绘图软件 V5.0')
window.geometry('800x400+400+200')
window.minsize(800, 400)
menubar = tk.Menu(window)
filemenu = tk.Menu(menubar, tearoff=0)
editmenu = tk.Menu(menubar, tearoff=0)
aboutmenu = tk.Menu(menubar, tearoff=0)

# 创建气温色带
temperature_colors_warm = ['#D8F20C', '#FFDA05', '#E6A216', '#FC760D', '#F53F18']  # 气温暖色
cmaps_tem_p = colors.LinearSegmentedColormap.from_list('mycmap', temperature_colors_warm)  # 正气温色带
temperature_colors_cool = ['#80419D', '#069CEE', '#52CC8D', '#50CA4B', '#EFFF2D']  # 气温冷色
cmaps_tem_n = colors.LinearSegmentedColormap.from_list('mycmap', temperature_colors_cool)  # 负气温色带
temperature_colors = temperature_colors_cool + temperature_colors_warm  # 正负气温
cmaps_tem = colors.LinearSegmentedColormap.from_list('mycmap', temperature_colors)  # 正负气温生成色带

# 创建降水色带
# colorslist = ['dodgerblue', 'blue', 'green', 'chartreuse', 'yellow',
#               'red']  # 'darkturquoise','lightblue','royalblue' 降水色标
rain_levels = [0, 0.1, 10, 25, 50, 100, 250, 25000]
rain_colors = ['#FFFFFF', '#A6F28F', '#38A800', '#61B8FF', '#0000FF', '#FA00FA', '#730000', '#400000']
cmaps_pre = colors.LinearSegmentedColormap.from_list('mycmap', rain_colors)  # CMA标准降水量色带

rain_colors_p = ['#EFFF2D', '#50CA4B', '#52CC8D', '#069CEE', '#80419D']  # 降水正距平百分率颜色
cmaps_pre_p = colors.LinearSegmentedColormap.from_list('mycmap', rain_colors_p)  # 创建降水正距平百分率色带

rain_colors_n = temperature_colors_warm  # 降水负距平百分率颜色
cmaps_pre_n = colors.LinearSegmentedColormap.from_list('mycmap', rain_colors_n)  # 创建降水负距平百分率色带

rain_anomaly = ['#F53F18', '#FC760D', '#E6A216', '#FFDA05', '#D8F20C'] + rain_colors_p
cmaps_pre_anomaly = colors.LinearSegmentedColormap.from_list('mycmap', rain_anomaly)  # 创建降水距平百分率色带


def conver_titles(file_path):  # 格式转换（系统生成的titles与数据不匹配）
    global df
    df0 = pd.read_csv(file_path, sep=',', encoding='GB2312')
    df1 = pd.read_csv(file_path, sep=',', encoding='GB2312', header=1)
    title_name = list(df0.columns)
    title_name.extend(['Unnamed' + str(i) for i in range(df1.shape[1] - len(title_name))])
    df = pd.read_csv(file_path, sep=',', encoding='GB2312', header=0, names=title_name)
    return df


def road_data(*args):
    global file_path  # glabal作用是整个程序都存在这个变量，如果不加这句，只在open_file函数下有这个变量
    # file_path = filedialog.askopenfilename()
    file_path = '../temp.txt'
    conver_titles(file_path)
    df_temp = pd.read_csv(file_path, sep=',', encoding='GB2312')
    colname = df_temp.columns.values.tolist()
    colname.insert(0, '请选择...')
    btn_sectdata['value'] = colname
    btn_sectdata.current(0)  # 选择数据恢复默认值选项
    btn_sectlevels.current(0) #色阶级数恢复默认值选项
    entry_var7.set('默认')
    entry_var8.set('默认')
    return file_path


def donothing():
    pass


def selectedcol(*args):
    global z
    z = df[btn_sectdata.get()]
    return z


def color_levels(*args):
    global mark1_1, mnum_1, markclick
    markclick = 1
    if btn_sectlevels.get() == '默认':
        mark1_1 = 0
        mnum_1 = None
    else:
        mark1_1 = 1
        mnum_1 = int(btn_sectlevels.get()) + 1
    return mark1_1, mnum_1, markclick


# ----------实现复制到系统剪切板功能----------------
def send_msg_to_clip(type_data, msg):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(type_data, msg)
    win32clipboard.CloseClipboard()


def paste_img(file_img):
    image = Image.open(file_img)
    output = BytesIO()
    image.convert('RGB').save(output, 'BMP')
    data = output.getvalue()[14:]
    output.close()
    send_msg_to_clip(win32clipboard.CF_DIB, data)


def docopy(*args):
    paste_img('pics_dpi300.png')


# ----------实现自定义色块功能----------------
def sect_color1():
    color = askcolor(title='自定义颜色')
    name_canvas[1].config(bg=color[1])
    rgb[0] = color[1]


def sect_color2():
    color = askcolor(title='自定义颜色')
    name_canvas[2].config(bg=color[1])
    rgb[1] = color[1]


def sect_color3():
    color = askcolor(title='自定义颜色')
    name_canvas[3].config(bg=color[1])
    rgb[2] = color[1]


def sect_color4():
    color = askcolor(title='自定义颜色')
    name_canvas[4].config(bg=color[1])
    rgb[3] = color[1]


def sect_color5():
    color = askcolor(title='自定义颜色')
    name_canvas[5].config(bg=color[1])
    rgb[4] = color[1]


def sect_color6():
    color = askcolor(title='自定义颜色')
    name_canvas[6].config(bg=color[1])
    rgb[5] = color[1]


def sect_color7():
    color = askcolor(title='自定义颜色')
    name_canvas[7].config(bg=color[1])
    rgb[6] = color[1]


def sect_color8():
    color = askcolor(title='自定义颜色')
    name_canvas[8].config(bg=color[1])
    rgb[7] = color[1]


def sect_color9():
    color = askcolor(title='自定义颜色')
    name_canvas[9].config(bg=color[1])
    rgb[8] = color[1]


def sect_color10():
    color = askcolor(title='自定义颜色')
    name_canvas[10].config(bg=color[1])
    rgb[9] = color[1]


def selected_cmap(*args):
    global color_mark, name_canvas, rgb
    if btn_style.get() == '气温(距平)色带':
        color_mark = 1
    elif btn_style.get() == '降水色带':
        color_mark = 2
    elif btn_style.get() == '日照色带':
        color_mark = 3
    elif btn_style.get() == '降水距平色带':
        color_mark = 4
    elif btn_style.get() == 'CMA雨色带':
        color_mark = 5
    elif btn_style.get() == '自定义...':
        color_mark = 6
        rgb = [None] * 10  # 最多存10级颜色
        colorsetting = tk.Tk()  # 导入tkinter中的tk模块
        colorsetting.title('自定义颜色')
        colorsetting.geometry('300x550+1300+100')
        name_button = dict()
        name_canvas = dict()

        i = 1
        name_button[i] = tk.Button(colorsetting, text='第' + str(i) + '级颜色:', command=sect_color1)
        name_button[i].place(relx=40 / 300, rely=(i * 50 - 30) / 550, relwidth=0.3, relheight=0.08)
        name_canvas[i] = tk.Canvas(colorsetting, bg='white')
        name_canvas[i].place(relx=160 / 300, rely=(i * 50 - 30) / 550, relwidth=0.25, relheight=0.08)
        i = 2
        name_button[i] = tk.Button(colorsetting, text='第' + str(i) + '级颜色:', command=sect_color2)
        name_button[i].place(relx=40 / 300, rely=(i * 50 - 30) / 550, relwidth=0.3, relheight=0.08)
        name_canvas[i] = tk.Canvas(colorsetting, bg='white')
        name_canvas[i].place(relx=160 / 300, rely=(i * 50 - 30) / 550, relwidth=0.25, relheight=0.08)
        i = 3
        name_button[i] = tk.Button(colorsetting, text='第' + str(i) + '级颜色:', command=sect_color3)
        name_button[i].place(relx=40 / 300, rely=(i * 50 - 30) / 550, relwidth=0.3, relheight=0.08)
        name_canvas[i] = tk.Canvas(colorsetting, bg='white')
        name_canvas[i].place(relx=160 / 300, rely=(i * 50 - 30) / 550, relwidth=0.25, relheight=0.08)
        i = 4
        name_button[i] = tk.Button(colorsetting, text='第' + str(i) + '级颜色:', command=sect_color4)
        name_button[i].place(relx=40 / 300, rely=(i * 50 - 30) / 550, relwidth=0.3, relheight=0.08)
        name_canvas[i] = tk.Canvas(colorsetting, bg='white')
        name_canvas[i].place(relx=160 / 300, rely=(i * 50 - 30) / 550, relwidth=0.25, relheight=0.08)
        i = 5
        name_button[i] = tk.Button(colorsetting, text='第' + str(i) + '级颜色:', command=sect_color5)
        name_button[i].place(relx=40 / 300, rely=(i * 50 - 30) / 550, relwidth=0.3, relheight=0.08)
        name_canvas[i] = tk.Canvas(colorsetting, bg='white')
        name_canvas[i].place(relx=160 / 300, rely=(i * 50 - 30) / 550, relwidth=0.25, relheight=0.08)
        i = 6
        name_button[i] = tk.Button(colorsetting, text='第' + str(i) + '级颜色:', command=sect_color6)
        name_button[i].place(relx=40 / 300, rely=(i * 50 - 30) / 550, relwidth=0.3, relheight=0.08)
        name_canvas[i] = tk.Canvas(colorsetting, bg='white')
        name_canvas[i].place(relx=160 / 300, rely=(i * 50 - 30) / 550, relwidth=0.25, relheight=0.08)
        i = 7
        name_button[i] = tk.Button(colorsetting, text='第' + str(i) + '级颜色:', command=sect_color7)
        name_button[i].place(relx=40 / 300, rely=(i * 50 - 30) / 550, relwidth=0.3, relheight=0.08)
        name_canvas[i] = tk.Canvas(colorsetting, bg='white')
        name_canvas[i].place(relx=160 / 300, rely=(i * 50 - 30) / 550, relwidth=0.25, relheight=0.08)
        i = 8
        name_button[i] = tk.Button(colorsetting, text='第' + str(i) + '级颜色:', command=sect_color8)
        name_button[i].place(relx=40 / 300, rely=(i * 50 - 30) / 550, relwidth=0.3, relheight=0.08)
        name_canvas[i] = tk.Canvas(colorsetting, bg='white')
        name_canvas[i].place(relx=160 / 300, rely=(i * 50 - 30) / 550, relwidth=0.25, relheight=0.08)
        i = 9
        name_button[i] = tk.Button(colorsetting, text='第' + str(i) + '级颜色:', command=sect_color9)
        name_button[i].place(relx=40 / 300, rely=(i * 50 - 30) / 550, relwidth=0.3, relheight=0.08)
        name_canvas[i] = tk.Canvas(colorsetting, bg='white')
        name_canvas[i].place(relx=160 / 300, rely=(i * 50 - 30) / 550, relwidth=0.25, relheight=0.08)
        i = 10
        name_button[i] = tk.Button(colorsetting, text='第' + str(i) + '级颜色:', command=sect_color10)
        name_button[i].place(relx=40 / 300, rely=(i * 50 - 30) / 550, relwidth=0.3, relheight=0.08)
        name_canvas[i] = tk.Canvas(colorsetting, bg='white')
        name_canvas[i].place(relx=160 / 300, rely=(i * 50 - 30) / 550, relwidth=0.25, relheight=0.08)


def draw_function():
    if markclick == 0:  # mclick 如果不存在，则鼠标未点击色阶级数，则给mark1和mnum赋初始值
        mark1 = 0
        mnum = None
    else:
        mark1 = mark1_1
        mnum = mnum_1
    if btn_legendmin.get() == '默认':
        mark2 = 0
        mmin = None
    else:
        mark2 = 1
        mmin = float(btn_legendmin.get())
    if btn_legendmax.get() == '默认':
        mark3 = 0
        mmax = None
    else:
        mark3 = 1
        mmax = float(btn_legendmax.get())
        if mmax <= mmin:
            tm.showwarning('警告', '图例最大值应大于最小值！')

    # ------------警告提示框---------
    if (mark1 == 0 or mark1 == 1) and mark2 == 0 and mark3 == 0:
        pass
    elif color_mark == 6:
        pass
    elif mark1 == 0 and (mark2 == 1 or mark3 == 1):
        tm.showwarning('警告', '色阶级数默认情况下，图例最小值和图例最大值均应为“默认”。')
        return
    elif mark1 == 1 and mark2 == 1 and mark3 == 1:
        pass
    else:
        tm.showinfo('提示', '色阶级数非默认情况下，需同时自定义设置图例最小值和图例最大值；否则图例最大值和最小值以默认值绘出。')
        pass

    path0 = 'JXshp/dishi.shp'
    file = shapefile.Reader(path0)
    rec = file.shapeRecords()
    polygon = list()
    for r in rec:
        polygon.append(Polygon(r.shape.points))
    poly = unary_union(polygon)  # 并集
    ext = list(poly.exterior.coords)  # 外部点
    codes = [Path.MOVETO] + [Path.LINETO] * (len(ext) - 1) + [Path.CLOSEPOLY]
    #    codes += [Path.CLOSEPOLY]
    ext.append(ext[0])  # 起始点
    path = Path(np.array(ext), codes)
    patch = PathPatch(path, facecolor='None')

    x, y = df['经度'], df['纬度']
    xi = np.arange(113, 118.5, 0.01)
    yi = np.arange(24, 31, 0.01)
    olon, olat = np.meshgrid(xi, yi)

    # Rbf空间插值
    func = Rbf(x, y, z, function='linear')
    oz = func(olon, olat)

    # 克里金插值
    # ok = OrdinaryKriging(x, y, z, variogram_model='linear')
    # oz, ss = ok.execute('grid', xi, yi)

    ax = plt.axes(projection=ccrs.PlateCarree())
    box = [113.4, 118.7, 24.1, 30.4]
    ax.set_extent(box, crs=ccrs.PlateCarree())
    ax.add_patch(patch)
    shp = list(shpreader.Reader(path0).geometries())
    # ax.add_geometries(shp, ccrs.PlateCarree(), edgecolor='black',
    #                   facecolor='none', alpha=0.3, linewidth=0.5)  # 加底图
    if mark1 == 1 and mark2 == 1 and mark3 == 1 and btn_style.get() != 'CMA雨色带' \
            and btn_style.get() != '自定义...':
        v = np.linspace(mmin, mmax, num=mnum, endpoint=True)  # 设置显示数值范围和级数
        if color_mark == 1:
            if np.min(oz) < 0 and np.max(oz) > 0:
                norm = colors.TwoSlopeNorm(vmin=np.min(oz), vcenter=0, vmax=np.max(oz))
                pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_tem, norm=norm)
            elif np.max(oz) < 0:
                pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_tem_n)
            else:
                pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_tem_p)
        elif color_mark == 2:
            pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_pre)
        elif color_mark == 3:
            pic = plt.contourf(olon, olat, oz, v, cmap=plt.cm.hot_r)
        elif color_mark == 4:
            if np.min(oz) < 0 and np.max(oz) > 0:
                norm = colors.TwoSlopeNorm(vmin=np.min(oz), vcenter=0, vmax=np.max(oz))
                pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_pre_anomaly, norm=norm)
            elif np.max(oz) < 0:
                pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_pre_n)
            else:
                pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_pre_p)
    elif btn_style.get() == 'CMA雨色带':
        # 应加入超出levels的提示
        try:
            pic = plt.contourf(olon, olat, oz, levels=rain_levels, colors=rain_colors)
            # cbar = plt.colorbar(pic, ticks=[0, 0.1, 10, 25, 50, 100, 250])
            # position = fig.add_axes([0.65, 0.15, 0.03, 0.3])  # 位置
            # plt.colorbar(pic, ticks=[0, 0.1, 10, 25, 50, 100, 250], cax=position, orientation='vertical')
            # cbar.set_label(btn9.get(), fontproperties='SimHei')  # 图例label在右边
        except:
            if np.min(z) < 0:
                tm.showinfo(message='存在负数，超出降水图例范围！请换其他颜色样式。')
            elif np.max(z) > 2500:
                tm.showinfo(message='降水量过大，请何查数据！或请换其他颜色样式。')
                # cbar.make_axes(locations='top')
        # cbar.ax.set_xlabel(btn9.get(),fontproperties='SimHei')
    else:
        if color_mark == 1:  # 气温色带
            if mark1 == 0:  # 未设置色带级数
                if np.min(oz) < 0 and np.max(oz) > 0:
                    norm = colors.TwoSlopeNorm(vmin=np.min(oz), vcenter=0, vmax=np.max(oz))
                    pic = plt.contourf(olon, olat, oz, cmap=cmaps_tem, norm=norm)
                elif np.max(oz) < 0:
                    pic = plt.contourf(olon, olat, oz, cmap=cmaps_tem_n)
                else:
                    pic = plt.contourf(olon, olat, oz, cmap=cmaps_tem_p)
            else:  # 设置了级数
                v = np.linspace(np.min(oz), np.max(oz), num=mnum, endpoint=True)  # 设置显示数值范围和级数
                if np.min(oz) < 0 and np.max(oz) > 0:
                    norm = colors.TwoSlopeNorm(vmin=np.min(oz), vcenter=0, vmax=np.max(oz))
                    pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_tem, norm=norm)
                elif np.max(oz) < 0:
                    pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_tem_n)
                else:
                    pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_tem_p)
        elif color_mark == 2:  # 降水色带
            if mark1 == 0:  # 未设置色带级数
                pic = plt.contourf(olon, olat, oz, cmap=cmaps_pre)
            else:
                v = np.linspace(np.min(oz), np.max(oz), num=mnum, endpoint=True)
                pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_pre)
        elif color_mark == 3:  # 日照时数色带
            if mark1 == 0:  # 未设置色带级数
                pic = plt.contourf(olon, olat, oz, cmap=plt.cm.hot_r)
            else:
                v = np.linspace(np.min(oz), np.max(oz), num=mnum, endpoint=True)
                pic = plt.contourf(olon, olat, oz, v, cmap=plt.cm.hot_r)
        elif color_mark == 4:
            if mark1 == 0:  # 未设置色带级数
                if np.min(oz) < 0 and np.max(oz) > 0:
                    norm = colors.TwoSlopeNorm(vmin=np.min(oz), vcenter=0, vmax=np.max(oz))
                    pic = plt.contourf(olon, olat, oz, cmap=cmaps_pre_anomaly, norm=norm)
                elif np.max(oz) < 0:
                    pic = plt.contourf(olon, olat, oz, cmap=cmaps_pre_n)
                else:
                    pic = plt.contourf(olon, olat, oz, cmap=cmaps_pre_p)
            else:
                v = np.linspace(np.min(oz), np.max(oz), num=mnum, endpoint=True)
                if np.min(oz) < 0 and np.max(oz) > 0:
                    norm = colors.TwoSlopeNorm(vmin=np.min(oz), vcenter=0, vmax=np.max(oz))
                    pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_pre_anomaly, norm=norm)
                elif np.max(oz) < 0:
                    pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_pre_n)
                else:
                    pic = plt.contourf(olon, olat, oz, v, cmap=cmaps_pre_p)
        elif color_mark == 6:  # 自定义颜色
            # 判断出自定义颜色级数
            jishu_colors = []
            for index, r in enumerate(rgb):
                if r == None:
                    num_color = index
                    break
                else:
                    jishu_colors.append(r)

            if mark2 == 1 and mark3 == 1:  # mark2最小值；mark3最大值
                v = np.linspace(mmin, mmax, num=num_color + 1, endpoint=True)  # 设置显示数值范围和级数
                pic = plt.contourf(olon, olat, oz, v, colors=jishu_colors)
            else:
                v = np.linspace(np.min(oz), np.max(oz), num=len(jishu_colors) + 1, endpoint=True)
                pic = plt.contourf(olon, olat, oz, v, colors=jishu_colors)

    for collection in pic.collections:
        collection.set_clip_path(patch)  # 设置显示区域

    plt.scatter(x, y, marker='.', c='k', s=10)  # 绘制站点

    # 添加显示站名、数值等标签
    for i in range(len(z)):
        plt.text(x[i], y[i] + 0.05, df['站名'][i], size=5.5, weight=2, wrap=True)
    # 添加单位标注
    plt.text(117.75, 27.1, btn_legendunit.get(), size=8, weight=2)
    # 添加地市边界
    ax.add_geometries(shp, ccrs.PlateCarree(), edgecolor='black',
                      facecolor='none', alpha=0.3, linewidth=0.5)  # 加底图

    fig = plt.gcf()
    fig.set_size_inches(6, 4)  # 设置图片大小
    plt.axis('off')  # 去除四边框框
    # 图例
    if btn_style.get() == 'CMA雨色带':
        position = fig.add_axes([0.65, 0.15, 0.03, 0.3])  # 位置
        plt.colorbar(pic, ticks=[0, 0.1, 10, 25, 50, 100, 250], cax=position, orientation='vertical')
    else:
        position = fig.add_axes([0.65, 0.15, 0.03, 0.3])  # 位置
        plt.colorbar(pic, cax=position, orientation='vertical')

    plt.savefig('pics_dpi100.png', dpi=100, bbox_inches='tight')
    plt.savefig('pics_dpi300.png', dpi=300, bbox_inches='tight')
    plt.close()
    wifi_img = Image.open('pics_dpi100.png')
    img = ImageTk.PhotoImage(wifi_img)
    window.img = img  # to prevent the image garbage collected.
    canvas.create_image(200, 180, anchor='center', image=img)  # 设置生成的图片位置


def introduction():  # 软件介绍函数
    # 弹出对话框
    tm.showinfo(title='软件说明', message=
    '功能：对接气候评价业务系统，实现快速绘图。\n\
\n插值方法：Rbf\n\
\n操作说明：载入评价系统生成的txt文件 --> 绘图设置 --> 绘图 --> 复制粘贴至Word\n\
\n注意事项：\n\n1. 若色阶级数选择默认，则图例最大值和图例最小值无需修改，保持默认;'
    '\n\n2. 软件应放评价系统目录下。')


def update_message():  # 软件更新说明函数
    tm.showinfo(title='更新说明', message='1. 解决了部分电脑无法显示中文的问题;\n\n 2. 参考QX/T180-2013标准设置色带;\n\n'
                                      '3. 对加载数据做了优化，无需手动加载数据文件')


if __name__ == '__main__':
    menubar.add_cascade(label='文件(F)', menu=filemenu)
    # filemenu.add_command(label='新建(N)', command = donothing)
    # filemenu.add_command(label='导入数据', command = donothing)
    # submenu = tk.Menu(filemenu,tearoff = 0)
    # filemenu.add_cascade(label='新建(N)',menu=submenu)
    menubar.add_cascade(label='编辑(E)', menu=editmenu)
    menubar.add_cascade(label='关于(A)', menu=aboutmenu)
    aboutmenu.add_command(label='软件说明', command=introduction)
    aboutmenu.add_command(label='更新说明', command=update_message)
    window.config(menu=menubar)

    btn_input = tk.Button(window, text='加载数据', command=road_data)
    # btn1.grid(row = 0,column = 110,ipadx=20,ipady=10)
    # btn1.place(x=100,y=100, width = 70, height= 50)
    btn_input.place(relx=100 / 800, rely=30 / 800, relwidth=0.1, relheight=0.1)

    btn_draw = tk.Button(window, text='绘图', command=draw_function)
    # btn2.grid(row = 1,column = 111,columnspan = 2,ipadx=20,ipady=10)
    btn_draw.place(relx=100 / 800, rely=670 / 800, relwidth=0.1, relheight=0.1)

    text1 = tk.Label(window, text='请选择插值要素：')
    text1.place(relx=30 / 800, rely=180 / 800)
    btn_sectdata = ttk.Combobox(window, state='readonly')
    btn_sectdata.place(relx=140 / 800, rely=180 / 800, relwidth=0.1)
    btn_sectdata['value'] = ('请选择...')
    btn_sectdata.current(0)  # 默认值
    btn_sectdata.bind("<<ComboboxSelected>>", selectedcol)

    text2 = tk.Label(window, text='请设置色阶级数：')
    text2.place(relx=30 / 800, rely=260 / 800)
    markclick = 0

    btn_sectlevels = ttk.Combobox(window, state='readonly')
    btn_sectlevels.place(relx=140 / 800, rely=260 / 800, relwidth=0.1)
    btn_sectlevels['value'] = ('默认', '3', '4', '5', '6', '7', '8', '9', '10', '11')
    btn_sectlevels.current(0)  # 默认值
    btn_sectlevels.bind("<<ComboboxSelected>>", color_levels)

    text3 = tk.Label(window, text='请输入图例最小值：')
    text3.place(relx=30 / 800, rely=340 / 800)
    entry_var7 = tk.StringVar()
    btn_legendmin = ttk.Entry(window, textvariable=entry_var7)
    btn_legendmin.place(relx=140 / 800, rely=340 / 800, relwidth=0.1)
    entry_var7.set('默认')

    text4 = tk.Label(window, text='请输入图例最大值：')
    text4.place(relx=30 / 800, rely=420 / 800)
    entry_var8 = tk.StringVar()
    btn_legendmax = ttk.Entry(window, textvariable=entry_var8)
    btn_legendmax.place(relx=140 / 800, rely=420 / 800, relwidth=0.1)
    entry_var8.set('默认')

    text5 = tk.Label(window, text='请输入图例单位：')
    text5.place(relx=30 / 800, rely=500 / 800)
    entry_var9 = tk.StringVar()
    btn_legendunit = ttk.Entry(window, textvariable=entry_var9)
    btn_legendunit.place(relx=140 / 800, rely=500 / 800, relwidth=0.1)
    entry_var9.set('(℃)')

    text6 = tk.Label(window, text='请选择颜色样式：')
    text6.place(relx=30 / 800, rely=580 / 800)
    btn_style = ttk.Combobox(window, state='readonly')
    btn_style.place(relx=140 / 800, rely=580 / 800, relwidth=0.1)
    btn_style['value'] = ('请选择...', '气温(距平)色带', '降水色带', '降水距平色带', '日照色带', 'CMA雨色带', '自定义...')
    btn_style.current(0)  # 默认值
    btn_style.bind("<<ComboboxSelected>>", selected_cmap)

    # 画布设置
    canvas = tk.Canvas(window, bg='white')
    canvas.place(relx=300 / 800, rely=20 / 400, relwidth=0.5, relheight=0.9)
    menucopy = tk.Menu(window, tearoff=0)
    menucopy.add_command(label="复制", command=docopy)


    def popupmenu(event):
        menucopy.post(event.x_root, event.y_root)


    canvas.bind("<Button-3>", popupmenu)  # 绑定鼠标右键
    window.mainloop()
