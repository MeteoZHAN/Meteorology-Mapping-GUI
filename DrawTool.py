# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 08:48:21 2019

@author: ZhanLF
"""

import tkinter as tk
from tkinter import filedialog, ttk
import tkinter.messagebox as tm
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from PIL import Image, ImageTk
import cartopy.io.shapereader as shpreader
from scipy.interpolate import Rbf
from shapely.ops import cascaded_union
import shapefile
# import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
import numpy as np
import cartopy.crs as ccrs
from io import BytesIO
import win32clipboard

# font_custum = FontProperties(fname=r"C:\WINDOWS\Fonts\simsun.ttc", size=6)
plt.rcParams['font.sans-serif'] = ['STSong']  # 用来正常显示中文字符

window = tk.Tk()
window.title('空间插值绘图小工具 V1.0')
window.geometry('800x400+400+200')
window.minsize(800, 400)
menubar = tk.Menu(window)
filemenu = tk.Menu(menubar, tearoff=0)
editmenu = tk.Menu(menubar, tearoff=0)
aboutmenu = tk.Menu(menubar, tearoff=0)


def open_file(*args):
    global file_path, df, colname  # glabal作用是整个程序都存在这个变量，如果不加这句，只在open_file函数下有这个变量
    file_path = filedialog.askopenfilename()
    df = pd.read_csv(file_path, sep=',', encoding='GB2312')
    colname = df.columns.values.tolist()
    colname.insert(0, '请选择...')
    btn5['value'] = colname
    btn5.current(0)  # 默认值
    return file_path, df, colname


def donothing():
    pass


def selectedcol(*args):
    global z
    z = df[btn5.get()]
    return z


def jishu(*args):
    global mark1, mnum
    if btn6.get() == '默认':
        mark1 = 0
        mnum = None
    else:
        mark1 = 1
        mnum = int(btn6.get()) + 1
    return mark1, mnum


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
    paste_img('pics.png')


def selected_cmap(*args):
    global color_mark
    if btn10.get() == 'jet':
        color_mark = 1
    elif btn10.get() == 'rainbow':
        color_mark = 2
    elif btn10.get() == 'gist_rainbow':
        color_mark = 3
    elif btn10.get() == 'OrRd':
        color_mark = 4
    elif btn10.get() == 'CMA_Rain':
        color_mark = 5
    return color_mark


def draw_function():
    if btn7.get() == '默认':
        mark2 = 0
        mmin = None
    else:
        mark2 = 1
        mmin = float(btn7.get())
    if btn8.get() == '默认':
        mark3 = 0
        mmax = None
    else:
        mark3 = 1
        mmax = float(btn8.get())

    # ------------警告提示框---------
    if mark1 == 0 and mark2 == 0 and mark3 == 0:
        pass
    elif mark1 == 0 and (mark2 == 1 or mark3 == 1):
        tm.showwarning('警告', '色阶级数默认情况下，图例最小值和图例最大值均应为“默认”。')
        return
    elif mark1 == 1 and mark2 == 1 and mark3 == 1:
        pass
    else:
        tm.showinfo('提示', '色阶级数非默认情况下，需同时自定义设置图例最小值和图例最大值；否则图例最大值和最小值以默认值绘出。')
        pass

    path0 = 'DTool/dishi.shp'
    #    path1 = 'C:/Users/zhanLf/Desktop/Python/DTool/shengjie.shp'
    #    a = gpd.GeoDataFrame.from_file(r'C:\Users\zhanlf\Desktop\Python\DTool\dishi.shp')

    file = shapefile.Reader(path0)
    rec = file.shapeRecords()
    polygon = list()
    for r in rec:
        polygon.append(Polygon(r.shape.points))
    poly = cascaded_union(polygon)  # 并集
    ext = list(poly.exterior.coords)  # 外部点
    codes = [Path.MOVETO] + [Path.LINETO] * (len(ext) - 1) + [Path.CLOSEPOLY]
    #    codes += [Path.CLOSEPOLY]
    ext.append(ext[0])  # 起始点
    path = Path(np.array(ext), codes)
    patch = PathPatch(path, facecolor='None')
    df0 = pd.read_csv(file_path, sep=',', encoding='GB2312')
    df1 = pd.read_csv(file_path, sep=',', encoding='GB2312', header=1)
    title_name = list(df0.columns)
    title_name.extend(['Unnamed' + str(i) for i in range(df1.shape[1] - len(title_name))])
    df = pd.read_csv(file_path, sep=',', encoding='GB2312', header=0, names=title_name)
    x, y = df['经度'], df['纬度']
    xi = np.arange(113, 118.5, 0.01)
    yi = np.arange(24, 31, 0.01)
    olon, olat = np.meshgrid(xi, yi)

    # 空间插值计算
    func = Rbf(x, y, z, function='linear')
    rain_data_new = func(olon, olat)

    ax = plt.axes(projection=ccrs.PlateCarree())
    box = [113.4, 118.7, 24.1, 30.4]
    ax.set_extent(box, crs=ccrs.PlateCarree())
    ax.add_patch(patch)
    shp = list(shpreader.Reader(path0).geometries())
    ax.add_geometries(shp, ccrs.PlateCarree(), edgecolor='black',
                      facecolor='none', alpha=1, linewidth=0.5)  # 加底图

    '''    不可取方法，太耗时间
    #for i in range(0,olat.shape[1]):
    #    print(i)
    #    for j in range(0,olat.shape[0]):
    #        if geometry.Point(np.array([olon[0,i],olat[j,0]])).within(geometry.shape(shps)): 
    #            continue
    #        else:
    #            rain_data_new[j,i] = np.nan
    '''

    if mark1 == 1 and mark2 == 1 and mark3 == 1 and btn10.get() != 'CMA_Rain':
        v = np.linspace(mmin, mmax, num=mnum, endpoint=True)  # 设置显示数值范围和级数
        if color_mark == 1:
            pic = plt.contourf(olon, olat, rain_data_new, v, cmap=plt.cm.jet)
        elif color_mark == 2:
            pic = plt.contourf(olon, olat, rain_data_new, v, cmap=plt.cm.rainbow)
        elif color_mark == 3:
            pic = plt.contourf(olon, olat, rain_data_new, v, cmap=plt.cm.gist_rainbow)
        elif color_mark == 4:
            pic = plt.contourf(olon, olat, rain_data_new, v, cmap=plt.cm.OrRd)
        cbar = plt.colorbar(pic)
        # cbar.set_label(btn9.get(),fontproperties='STSong') #图例label在右边


    # elif mark1 == 1 and mark2 == 0 and mark3 == 0 and btn10.get() != 'CMA_Rain':
    #     # if color_mark == 1:
    #     #     pic = plt.contourf(olon, olat, rain_data_new, mnum, cmap = plt.cm.jet)
    #     # elif color_mark == 2:
    #     #     pic = plt.contourf(olon, olat, rain_data_new, mnum, cmap = plt.cm.rainbow)
    #     # elif color_mark == 3:
    #     #     pic = plt.contourf(olon, olat, rain_data_new, mnum, cmap = plt.cm.gist_rainbow)
    #     # elif color_mark == 4:
    #     #     pic = plt.contourf(olon, olat, rain_data_new, mnum, cmap = plt.cm.OrRd)
    #     # v = np.linspace(mmin, mmax, num = mnum, endpoint = True)
    #     pic = plt.contourf(olon, olat, rain_data_new, mnum, cmap = plt.cm.jet)
    #     cbar = plt.colorbar(pic)
    #     cbar.set_label(btn9.get(),fontproperties='SimHei')
    elif btn10.get() == 'CMA_Rain':
        # 应加入超出levels的提示
        try:
            rain_levels = [0, 0.1, 10, 25, 50, 100, 250, 2500]
            rain_colors = ['#FFFFFF', '#A6F28F', '#38A800', '#61B8FF',
                           '#0000FF', '#FA00FA', '#730000', '#400000']
            pic = plt.contourf(olon, olat, rain_data_new, levels=rain_levels, colors=rain_colors)
            cbar = plt.colorbar(pic, ticks=[0, 0.1, 10, 25, 50, 100, 250])
            cbar.set_label(btn9.get(), fontproperties='SimHei')  # 图例label在右边
        except:
            if np.min(z) < 0:
                tm.showinfo(message='存在负数，超出降水图例范围！请换其他颜色样式。')
            elif np.max(z) > 2500:
                tm.showinfo(message='降水量过大，请何查数据！或请换其他颜色样式。')
                # cbar.make_axes(locations='top')
        # cbar.ax.set_xlabel(btn9.get(),fontproperties='SimHei')
    else:
        if color_mark == 1:
            pic = plt.contourf(olon, olat, rain_data_new, cmap=plt.cm.jet)
        elif color_mark == 2:
            pic = plt.contourf(olon, olat, rain_data_new, cmap=plt.cm.rainbow)
        elif color_mark == 3:
            pic = plt.contourf(olon, olat, rain_data_new, cmap=plt.cm.gist_rainbow)
        elif color_mark == 4:
            pic = plt.contourf(olon, olat, rain_data_new, cmap=plt.cm.OrRd)
        cbar = plt.colorbar(pic)
        # cbar.set_label(btn9.get(),fontproperties='SimHei') #图例label在右边  
        # plt.text(120.2, 30.35, btn9.get(), size = 8, weight = 2)

    for collection in pic.collections:
        collection.set_clip_path(patch)  # 设置显示区域

    plt.scatter(x, y, marker='.', c='k', s=10)  # 绘制站点

    # 添加显示站名、数值等标签
    for i in range(len(z)):
        plt.text(x[i], y[i] + 0.05, df['站名'][i], size=5.5, weight=2, wrap=True)
    # 添加单位标注
    plt.text(119.2, 30.6, btn9.get(), size=8, weight=2)

    # cbar.ax.set_xlabel(btn9.get(),fontproperties='SimHei') #图例label在下边

    fig = plt.gcf()
    fig.set_size_inches(6, 4)  # 设置图片大小
    plt.savefig('pics.png', bbox_inches='tight')
    plt.close()
    wifi_img = Image.open('pics.png')
    img = ImageTk.PhotoImage(wifi_img)
    window.img = img  # to prevent the image garbage collected.
    canvas.create_image(200, 180, anchor='center', image=img)  # 设置生成的图片位置


def introduction():  # 软件介绍函数
    # 弹出对话框
    tm.showinfo(title='软件说明', message=
    '功能：对接气候业务评价系统，实现业务快速绘图\n\
\n插值方法：采用径向基函数插值方法 func=Rbf(x,y,z,function = \'linear\')\n\
\n操作说明：载入评价系统生成的txt文件 --> 绘图设置 --> 绘图 --> 复\t\t制粘贴至Word\n\
\n注意事项：1.若色阶级数选择默认，则图例最大值和图例最小值无需修\t\t改，保持默认；\
否则，图例最大值和图例最小值均需自定义；\n\t2.shp文件应与该exe文件同目录')


def update():  # 软件更新说明函数
    tm.showinfo(title='更新说明', message='暂无')


if __name__ == '__main__':
    menubar.add_cascade(label='文件(F)', menu=filemenu)
    # filemenu.add_command(label='新建(N)', command = donothing)
    # filemenu.add_command(label='导入数据', command = donothing)
    # submenu = tk.Menu(filemenu,tearoff = 0)
    # filemenu.add_cascade(label='新建(N)',menu=submenu)
    menubar.add_cascade(label='编辑(E)', menu=editmenu)
    menubar.add_cascade(label='关于(A)', menu=aboutmenu)
    aboutmenu.add_command(label='软件说明', command=introduction)
    aboutmenu.add_command(label='更新说明', command=update)
    window.config(menu=menubar)

    btn1 = tk.Button(window, text='载入文件...', command=open_file)
    # btn1.grid(row = 0,column = 110,ipadx=20,ipady=10)
    # btn1.place(x=100,y=100, width = 70, height= 50)
    btn1.place(relx=100 / 800, rely=30 / 800, relwidth=0.1, relheight=0.1)

    btn2 = tk.Button(window, text='绘图', command=draw_function)
    # btn2.grid(row = 1,column = 111,columnspan = 2,ipadx=20,ipady=10)
    btn2.place(relx=100 / 800, rely=670 / 800, relwidth=0.1, relheight=0.1)

    # btn3 = tk.Radiobutton(window,text='jet')
    # btn3.place(relx=50/800,rely=150/800)

    # btn4 = tk.Radiobutton(window,text='bbbbb')
    # btn4.place(relx=50/800,rely=200/800)

    text1 = tk.Label(window, text='请选择插值要素：')
    text1.place(relx=30 / 800, rely=180 / 800)
    btn5 = ttk.Combobox(window, state='readonly')
    btn5.place(relx=140 / 800, rely=180 / 800, relwidth=0.1)
    btn5['value'] = ('请选择...')
    btn5.current(0)  # 默认值
    btn5.bind("<<ComboboxSelected>>", selectedcol)

    text2 = tk.Label(window, text='请设置色阶级数：')
    text2.place(relx=30 / 800, rely=260 / 800)
    btn6 = ttk.Combobox(window, state='readonly')
    btn6.place(relx=140 / 800, rely=260 / 800, relwidth=0.1)
    btn6['value'] = ('请选择...', '默认', '3', '4', '5', '6', '7', '8', '9', '10')
    btn6.current(0)  # 默认值
    btn6.bind("<<ComboboxSelected>>", jishu)

    text3 = tk.Label(window, text='请输入图例最小值：')
    text3.place(relx=30 / 800, rely=340 / 800)
    # btn7 = ttk.Combobox(window)
    # btn7.place(relx=130/800,rely=460/800,relwidth = 0.1)
    # btn7['value'] = ('默认','-8')
    # # btn7.current(0)#默认值
    # btn7.bind("<<ComboboxSelected>>",minvalue)
    entry_var7 = tk.StringVar()
    btn7 = ttk.Entry(window, textvariable=entry_var7)
    btn7.place(relx=140 / 800, rely=340 / 800, relwidth=0.1)
    entry_var7.set('默认')

    text4 = tk.Label(window, text='请输入图例最大值：')
    text4.place(relx=30 / 800, rely=420 / 800)
    # btn8 = ttk.Combobox(window)
    # btn8.place(relx=130/800,rely=540/800,relwidth = 0.1)
    # btn8['value'] = ('默认','-5')
    # # btn8.current(0)#默认值
    # btn8.bind("<<ComboboxSelected>>",maxvalue)
    entry_var8 = tk.StringVar()
    btn8 = ttk.Entry(window, textvariable=entry_var8)
    btn8.place(relx=140 / 800, rely=420 / 800, relwidth=0.1)
    entry_var8.set('默认')

    text5 = tk.Label(window, text='请输入图例单位：')
    text5.place(relx=30 / 800, rely=500 / 800)
    entry_var9 = tk.StringVar()
    btn9 = ttk.Entry(window, textvariable=entry_var9)
    btn9.place(relx=140 / 800, rely=500 / 800, relwidth=0.1)
    entry_var9.set('(℃)')

    text6 = tk.Label(window, text='请选择颜色样式：')
    text6.place(relx=30 / 800, rely=580 / 800)
    btn10 = ttk.Combobox(window, state='readonly')
    btn10.place(relx=140 / 800, rely=580 / 800, relwidth=0.1)
    btn10['value'] = ('请选择...', 'CMA_Rain', 'jet', 'rainbow', 'gist_rainbow', 'OrRd')
    btn10.current(0)  # 默认值
    btn10.bind("<<ComboboxSelected>>", selected_cmap)

    # 画布设置
    canvas = tk.Canvas(window, bg='white')
    canvas.place(relx=300 / 800, rely=20 / 400, relwidth=0.5, relheight=0.9)
    # canvas.bind("<Button-3>", docopy)

    menucopy = tk.Menu(window, tearoff=0)
    menucopy.add_command(label="复制", command=docopy)


    def popupmenu(event):
        menucopy.post(event.x_root, event.y_root)


    canvas.bind("<Button-3>", popupmenu)

    window.mainloop()
