'''需要用到的库：
    UI:PyQt5,pyqtgraph
    蓝牙:pybluez
'''
import sys
import time

from PyQt5.QtWidgets import (QWidget, QPushButton, QLineEdit,
                             QInputDialog, QApplication,QDesktopWidget,QFrame,QGridLayout,QLabel,QHBoxLayout,
                             QTextEdit,QVBoxLayout)
import pyqtgraph as pg
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QThread,pyqtSignal
import bluetooth
import traceback
import xlwt
from bluetooth.btcommon import BluetoothError
#定义一个线程类
class QThread_bthData(QThread):
    output=pyqtSignal(str)

    def __init__(self):
        super(QThread_bthData, self).__init__()
        self.working=True   #工作状态
        self.bth_work=True  #True为需要连接，连接后变为False
    def __del__(self):
        self.working=False
        self.wait()


    def run(self):
        #判断是否需要连接蓝牙
        if(self.bth_work==True):
            print("Performing inquiry...")
            str='Performing inquiry...'
            self.output.emit(str)
            # 搜索附近蓝牙设备并输出名字及地址信息
            nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True,
                                                        lookup_class=False)
            print("Found {} devices".format(len(nearby_devices)))
            for addr, name in nearby_devices:
                try:
                    print("   {} - {}".format(addr, name))
                except UnicodeEncodeError:
                    print("   {} - {}".format(addr, name.encode("utf-8", "replace")))

            # 在附近蓝牙设备中找到目标蓝牙，用sock方式连接，通讯协议为RFCOMM方式
            # 程序运行之前确保电脑与蓝牙设备已经连接，否侧会报错
            for addr, name in nearby_devices:
                addr_target = ''
                if name == 'BT04-A':
                    addr_target = addr
                    print(addr)
                    global sock
                    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                    try:
                        sock.connect((addr_target, 1))
                        print("Connection successful. Now ready to get the data")
                        str = 'Connection successful. Now ready to get the data'
                        self.output.emit(str)

                    except BluetoothError as e:
                        print("fail\n")
                        str = 'fail\n'
                        self.output.emit(str)
            self.bth_work=False    #连接成功后变为False，防止多次连接

        #接收蓝牙数据，并发送出去
        while self.working==True:
                try:
                    data = sock.recv(1024)
                    print(data)
                    data = data.decode('utf-8')
                    self.output.emit(data)
                except Exception as e:
                    print(traceback.print_exc())

#小车遥控线程
class QThread_control(QThread):
    def __init__(self, state_d_t,state):#state_d_t为转向或平移状态，state是转向中左转右转，或平移中前后左右状态
        super(QThread_control, self).__init__()
        #self.working=True
        self.state_d_t=state_d_t
        self.state=state
    def __del__(self):
        #self.working=False
        self.wait()
    def run(self):
        # while self.working==True:
        #
        #     sock.send(0x41)
        # sock.send('0')
        # time.sleep(0.5)
        # if(self.state=='W'):
        #
        #     sock.send('W')
        #     time.sleep(0.1)
        # elif(self.state=='S'):
        #     #
        #     sock.send('S')
        #     time.sleep(0.1)
        # elif(self.state=='A'):
        #     #while self.working==True:
        #     sock.send('A')
        #     time.sleep(0.1)
        # elif(self.state=='D'):
        #     #while self.working==True:
        #     sock.send('D')
        #     time.sleep(0.1)
        # elif(self.state=='P'):
        #     sock.send('P')
        #     time.sleep(0.1)
        #平移状态，state_d_t为‘D’
        if(self.state_d_t=='D'):
            sock.send('0')
            time.sleep(0.5)
            if (self.state == 'W'):
                #前
                sock.send('W')
                time.sleep(0.1)
            elif (self.state == 'S'):
                #后
                sock.send('S')
                time.sleep(0.1)
            elif (self.state == 'A'):
                #左
                sock.send('A')
                time.sleep(0.1)
            elif (self.state == 'D'):
                #右
                sock.send('D')
                time.sleep(0.1)
            elif (self.state == 'P'):
                #暂停平移
                sock.send('P')
                time.sleep(0.1)
        #转向状态，state_d_t为'T'
        elif(self.state_d_t=='T'):
            sock.send('Z')
            time.sleep(0.5)
            #右转
            if(self.state=='R'):
                sock.send('R')
                time.sleep(0.1)
            #左转
            elif(self.state=='L'):
                sock.send('L')
                time.sleep(0.1)



class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.IniteUI()    #UI布局
        self.generate_image()    #波形图画布
        self.generate_text()    #数据栏
        self.controlbutton()
        self.thread=QThread_bthData()    #初始化线程
        self.direction=''
        #self.thread_control=QThread_control(self.direction)

        #编码器与陀螺仪数据列表
        self.encoder_A = []
        self.encoder_B = []
        self.encoder_C = []
        self.encoder_D = []
        self.angel_x = []
        self.angel_y = []
    #设置UI
    def IniteUI(self):
        self.setGeometry(0, 0, 1800, 1200)
        self.center()
        self.setWindowTitle("实时接收蓝牙数据")
        self.gridLayout = QGridLayout(self)
        # 创建一个父容器-角度波形
        self.frame_angel = QFrame(self)
        self.frame_angel.setFrameShape(QFrame.Panel)  # 设置父容器的面板形式
        self.frame_angel.setFrameShadow(QFrame.Plain)  # 设置父容器边框阴影。
        self.frame_angel.setLineWidth(2)  # 设置父容器边框线宽
        self.frame_angel.setStyleSheet("background-color:rgb(0,255,255);")  # 设置表单颜色
        #创建一个父容器-编码器波形
        self.frame_encoder = QFrame(self)
        self.frame_encoder.setFrameShape(QFrame.Panel)  # 设置父容器的面板形式
        self.frame_encoder.setFrameShadow(QFrame.Plain)  # 设置父容器边框阴影。
        self.frame_encoder.setLineWidth(2)  # 设置父容器边框线宽
        self.frame_encoder.setStyleSheet("background-color:rgb(0,255,255);")  # 设置表单颜色
        # 创建一个父容器-数据输出
        self.frame_text = QFrame(self)
        self.frame_text.setFrameShape(QFrame.Panel)  # 设置父容器的面板形式
        self.frame_text.setFrameShadow(QFrame.Plain)  # 设置父容器边框阴影。
        self.frame_text.setLineWidth(2)  # 设置父容器边框线宽
        self.frame_text.setStyleSheet("background-color:rgb(255,255,255);")  # 设置表单颜色
        self.label = QLabel(self)
        # 创建一个父容器-控制按钮
        self.frame_control = QFrame(self)
        self.frame_control.setFrameShape(QFrame.Panel)  # 设置父容器的面板形式
        self.frame_control.setFrameShadow(QFrame.Plain)  # 设置父容器边框阴影。
        self.frame_control.setLineWidth(2)  # 设置父容器边框线宽
        self.frame_control.setStyleSheet("background-color:rgb(255,255,255);")  # 设置表单颜色
        self.label = QLabel(self)
        #初始化按钮
        #getData
        self.button_getData = QPushButton('getData', self)
        self.button_getData.clicked.connect(self.start)
        #stop
        self.button_stop = QPushButton('stop',self)
        self.button_stop.clicked.connect(self.end)
        #储存数据
        self.button_save = QPushButton('save', self)
        self.button_save.clicked.connect(self.saveData)
        #布局
        self.gridLayout.addWidget(self.frame_angel, 0, 0, 3, 5)  # griflayout的使用，将frame容器放在grid得一行
        self.gridLayout.addWidget(self.frame_encoder, 3, 0, 3, 5)
        self.gridLayout.addWidget(self.frame_text, 0, 5, 3, 3)
        self.gridLayout.addWidget(self.frame_control,3,5,2,3)
        self.gridLayout.addWidget(self.label, 5, 0, 1, 1)  # 将label和button，放在grid一行
        self.gridLayout.addWidget(self.button_getData, 5, 5, 1, 1)
        self.gridLayout.addWidget(self.button_stop, 5, 6, 1, 1)
        self.gridLayout.addWidget(self.button_save, 5, 7, 1, 1)
        self.setLayout(self.gridLayout)
    #将初始窗口放置在屏幕中心
    def center(self):
        qr=self.frameGeometry()
        cp=QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    #创建波形图
    def generate_image(self):
        #对角度波形图设置
        image_layout = QHBoxLayout(self.frame_angel)   #创建父容器后需要将graph添加到里面，采用QVBoxLaouth或者QHBoxLayout
        win_angel = pg.GraphicsLayoutWidget(self.frame_angel)  #将其显示在frame上
        image_layout.addWidget(win_angel)
        p = win_angel.addPlot(title = "")
        p.showGrid(x=True,y=True)
        p.setLabel(axis="left",text ="angel")
        p.setLabel(axis="bottom",text="time")
        p.setTitle("Angel Data")
        p.addLegend()
        self.curve_x = p.plot(pen="r",name="angel_x")#x方向的角度数据图像
        self.curve_y = p.plot(pen='g',name="angel_y")#y方向的角度数据图像

        #对编码器波形图设置
        image_layout = QHBoxLayout(self.frame_encoder)  # 创建父容器后需要将graph添加到里面，采用QVBoxLaouth或者QHBoxLayout
        win_encoder = pg.GraphicsLayoutWidget(self.frame_encoder)  # 将其显示在frame上
        image_layout.addWidget(win_encoder)
        p = win_encoder.addPlot(title="")
        p.showGrid(x=True, y=True)
        p.setLabel(axis="left", text="encoder")
        p.setLabel(axis="bottom", text="time")
        p.setTitle("encoder Data")
        p.addLegend()
        self.curve_A = p.plot(pen="r", name="encoder_A")  # x方向的角度数据图像
        self.curve_B = p.plot(pen='g', name="encoder_B")  # y方向的角度数据图像
        self.curve_C = p.plot(pen="y", name="encoder_C")  # x方向的角度数据图像
        self.curve_D = p.plot(pen="b", name="encoder_D")  # x方向的角度数据图像

    #数据显示窗口初始化
    def generate_text(self):
        text_layout = QVBoxLayout(self.frame_text)#竖直放置
        #建立两个文本框
        self.textedit_x = QTextEdit()
        self.textedit_y = QTextEdit()
        #添加到Widget
        text_layout.addWidget(self.textedit_x)
        text_layout.addWidget(self.textedit_y)

    #文本框显示文本
    def showstr(self,str):
        self.textedit_x.setText(str)

    #控制按钮
    def controlbutton(self):
        self.button_layout = QGridLayout(self.frame_control)

        self.button_forward = QPushButton('前', self)
        self.button_forward.clicked.connect(self.move_forward)

        self.button_back = QPushButton('后', self)
        self.button_back.clicked.connect(self.move_back)

        self.button_left = QPushButton('左', self)
        self.button_left.clicked.connect(self.move_left)

        self.button_right = QPushButton('右', self)
        self.button_right.clicked.connect(self.move_right)

        self.button_movestop = QPushButton('停止',self)
        self.button_movestop.clicked.connect(self.move_stop)

        self.button_turnright = QPushButton('右转', self)
        self.button_movestop.clicked.connect(self.turn_right)

        self.button_turnleft = QPushButton('左转', self)
        self.button_movestop.clicked.connect(self.turn_left)

        self.button_layout.addWidget(self.button_forward, 0, 1, 1, 1)
        self.button_layout.addWidget(self.button_back, 2, 1, 1, 1)
        self.button_layout.addWidget(self.button_left, 1, 0, 1, 1)
        self.button_layout.addWidget(self.button_right, 1, 2, 1, 1)
        self.button_layout.addWidget(self.button_turnright, 0, 0, 1, 1)
        self.button_layout.addWidget(self.button_turnleft, 0, 2, 1, 1)
        self.button_layout.addWidget(self.button_movestop, 1, 1, 1, 1)

    #发送控制指令
    # def moveStart(self):
    #     if self.button_forward.isChecked(self):
    #         print('forward')
    #         self.thread_control = QThread_control('A')
    #         self.thread_control.start()
    #     elif self.button_back.isChecked():
    #         self.thread_control = QThread_control('B')
    #         self.thread_control.start()
    #     elif self.button_left.isChecked():
    #         self.thread_control = QThread_control('C')
    #         self.thread_control.start()
    #     elif self.button_right.isChecked():
    #         self.thread_control = QThread_control('D')
    #         self.thread_control.start()
    def move_forward(self):
        self.thread_control = QThread_control('T', 'W')
        self.thread_control.start()

    def move_back(self):
        self.thread_control = QThread_control('T', 'S')
        self.thread_control.start()

    def move_left(self):
        self.thread_control = QThread_control('T', 'A')
        self.thread_control.start()

    def move_right(self):
        self.thread_control = QThread_control('T', 'D')
        self.thread_control.start()

    def turn_right(self):
        self.thread_control = QThread_control('D', 'R')
        self.thread_control.start()

    def turn_left(self):
        self.thread_control = QThread_control('D', 'L')
        self.thread_control.start()

    def move_stop(self):
        self.thread_control = QThread_control('T', 'P')
        self.thread_control.start()

    #蓝牙线程开始工作
    def start(self):
        self.thread.start()
        self.thread.output.connect(self.plotData)
        self.thread.output.connect(self.showstr)
        self.button_getData.setText("renew")
        self.button_getData.clicked.connect(self.renew)
    #蓝牙线程暂停
    def end(self):
        self.thread.working=False
    #线程恢复工作
    def renew(self):
        self.thread.working=True

    #处理原始数据，得到编码器及陀螺仪数据
    def getData(self,data):
        if (data[1] == 'A'):
            #data = str(data, 'utf-8')
            data_re = data.replace('{', '')
            data_re = data_re.replace('}', '')
            data_re = data_re.replace('$', '')
            data_re = data_re.replace(data_re[0], '')
            data_re = data_re.split(':')
            #将data_re中数据转为float性，分别放入对应列表
            self.encoder_A.append(float(data_re[0]))
            self.encoder_B.append(float(data_re[1]))
            self.encoder_C.append(float(data_re[2]))
            self.encoder_D.append(float(data_re[3]))
        else:
            #data = str(data, 'utf-8')
            data_re = data.replace('{', '')
            data_re = data_re.replace('}', '')
            data_re = data_re.replace('$', '')
            data_re = data_re.replace(data_re[0], '')
            data_re = data_re.split(':')
            #data_re = re.findall("\d+", data)
            self.angel_x.append(float(data_re[0]))
            self.angel_y.append(float(data_re[1]))
            if (len(self.angel_x) > 60):
                del self.angel_x[0]
                del self.angel_y[0]
            else:
                self.angel_x = self.angel_x
                self.angel_y = self.angel_y
            # if (len(self.angel_y) > 60):
            #     del self.angel_y[0]
            # else:
            #     self.angel_y = self.angel_y
            #print("angel_x:",self.angel_x)
            #print("angel_y:", self.angel_y)

    #添加数据到波形图中，同时输出角度 x,y的数据
    def plotData(self,data):
        try:
            #data = data.decode('utf-8')
            self.getData(data)
            #画图
            self.curve_x.setData(self.angel_x)
            self.curve_y.setData(self.angel_y)
            self.curve_A.setData(self.encoder_A)
            self.curve_B.setData(self.encoder_B)
            self.curve_C.setData(self.encoder_C)
            self.curve_D.setData(self.encoder_D)
            str_x = "angel_x:" + str(self.angel_x[-1]) + "\n" + "angel_y:" + str(self.angel_y[-1]) + "\n"
            #str_y = "angel_y:" + str(self.angel_y[-1]) + "\n"
            self.textedit_y.setText(str_x)
            self.textedit_y.moveCursor(QTextCursor.End)
            # self.textedit_y.setText(str_y)
            # self.textedit_y.moveCursor(QTextCursor.End)
        except Exception as e:
            print(traceback.print_exc())

    def saveData(self):
        work=xlwt.Workbook(encoding='utf-8')
        sheet=work.add_sheet('data')
        sheet.write(0, 0, 'angel_x')
        sheet.write(0, 1, 'angel_y')
        count_x = 1
        count_y = 1
        for num_x in self.angel_x:
            sheet.write(count_x, 0, num_x)
            count_x+=1

        for num_y in self.angel_y:
            sheet.write(count_y, 1, num_y)
            count_y += 1

        nowtime = time.time()
        filename = str(nowtime)
        savename=filename + '.xls'
        work.save(savename)
        self.textedit_x.setText('save finished')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())