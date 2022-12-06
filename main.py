# -*- coding: utf-8 -*-
"""
Created on Mon Aug  2 01:00:47 2021

@author: rltjr
"""

import sys
from functools import partial
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread,pyqtSignal,pyqtSlot,Qt,QRect
from PyQt5.QtWidgets import QMainWindow,QTableWidgetItem,QMessageBox,QAction,QFileDialog,QApplication,QComboBox,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QWidget,QGridLayout
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from scipy import interpolate,signal



import Fitting

form_main = uic.loadUiType("gui/gui_main.ui")[0]

class Fitting_Thread(QThread):
    threadEvent = pyqtSignal()
    def __init__(self,parent):
        super().__init__(parent)
        self.main = parent
    def run(self):
        self.main.Fitting_Count = self.main.Fitting_Count + 1
        self.main.Fit.Fit()  #Fitting Start
        self.threadEvent.emit()
        

class MainClass(QMainWindow, form_main):
    def __init__(self):
        #initial setting
        super().__init__()
        self.setupUi(self)
        self.setAcceptDrops(True)
        
        self.name = "Optical Conductivity"
         
        self.Parameter.addWidget(self.Fit_Table)
        self.Parameter.addWidget(self.Fitting_Box)
        self.Back.setLayout(self.Layout)
        
        self.statusBar().addPermanentWidget(QLabel("Made by KKS"))
        
        
        #plt.rcParams['font.size'] = '16'
        self.setWindowTitle('Ellipsometry Fitting Program')
        self.setWindowIcon(QIcon('gui/icon.ico'))
        
        
        self.Plot_Init()
        self.menu_bar()
        self.c = 8065.5
        self.changedPosition = 0
        self.MaxIterations = 100
        self.Data_Point = 400 #For use Flat and Custom
        self.Data_Rate = 200  #For use Custom
        self.Weight_mode = 1 # 0:Raw,1:Flat,2:Drude
        self.Fit_number = 100 # Number of Fitting sequence per plot
        self.setting_value = []
        self.X = []
        self.Y = []
        self.Fit = Fitting.Function()
        
        
        # Setting Value
        self.Fitting_stop = False
        self.Fitting_Count = 0
        self.File_available =False
        self.Setting_available = False
        self.Table_List = [self.Variable_Table,self.Bound_A,self.Bound_Br,self.Bound_Xc] 
        self.Combo_Func_List = [] # Drude,Lorentz like func list
        # Func Setting line
        self.Func_New.clicked.connect(self.Func_New_Signal)
        self.Func_Delete.clicked.connect(self.Func_Delete_Signal)
        self.Func_Up.clicked.connect(self.Func_Up_Signal)
        self.Func_Down.clicked.connect(self.Func_Down_Signal)
        # Filter Setting
        self.Filter_Apply.clicked.connect(self.Filter_Active)
        # Weight Setting
        self.Weight_Raw.clicked.connect(self.Weight_Raw_toggled)
        self.Weight_Flat.clicked.connect(self.Weight_Flat_toggled)
        self.Weight_Drude.clicked.connect(self.Weight_Drude_toggled)
        self.Weight_Apply.clicked.connect(self.Weight_Apply_toggled)
        self.Weight_Points.valueChanged.connect(self.Weight_Points_toggled)
        self.Weight_Rate.valueChanged.connect(self.Weight_Rate_toggled)
        self.Weight_Rate_Bar.valueChanged.connect(self.Weight_Rate_Bar_toggled)
        # RT Setting
        self.RT_Value.valueChanged.connect(self.RT_Value_Changed)
        self.RT_On.toggled.connect(self.RT_On_Toggled)
        # Table Setting
        self.Fit_Table.currentChanged.connect(self.Fit_Table_Changed)
        # Init Table
        self.Variable_Table.setColumnCount(5)
        self.Table_List[0].currentCellChanged.connect(self.Cell_Entered)
        self.Table_List[0].cellChanged.connect(self.Cell_changed)
        # Bound_A Table
        self.Bound_A.setColumnCount(4)
        self.Table_List[1].currentCellChanged.connect(self.Cell_Entered)
        self.Table_List[1].cellChanged.connect(self.Cell_changed)
        # Bound_Br Table
        self.Bound_Br.setColumnCount(4)
        self.Table_List[2].currentCellChanged.connect(self.Cell_Entered)
        self.Table_List[2].cellChanged.connect(self.Cell_changed)
        # Bound_Xc Table
        self.Bound_Xc.setColumnCount(4)
        self.Table_List[3].currentCellChanged.connect(self.Cell_Entered)
        self.Table_List[3].cellChanged.connect(self.Cell_changed)
        # Other Setting
        self.Residual_Select.currentTextChanged.connect(self.Residual_Changed)
        self.LossFunction_Select.currentTextChanged.connect(self.LossFunction_Changed)
        self.Iterations.valueChanged.connect(self.Iterations_changed)
        self.Fit_button.clicked.connect(self.Fit_Func) 
        self.Abort_button.clicked.connect(self.Abort_Func)
        # Fitting Range setting
        self.Range_button.clicked.connect(self.Fitting_changed)
        
    #File Drop
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
 
    def dropEvent(self, event):
        data = [u.toLocalFile() for u in event.mimeData().urls()]
        self.FileLoadFunc(drop_file = data)
        
    ##### Tool Line #####
    def Update(self):
        for i in range(4):
            self.Table_Changer(i)
        self.Plot_Setting()
    def Func_Setting_Button_Control(self,enable):
        self.Func_New.setEnabled(enable)
        self.Func_Delete.setEnabled(enable)
        self.Func_Up.setEnabled(enable)
        self.Func_Down.setEnabled(enable)
        if len(self.Fit.Init) == 0: # if Deleted Func were last one
            self.Func_Delete.setEnabled(False)
            self.Func_Up.setEnabled(False)
            self.Func_Down.setEnabled(False)
    def Decode(self,Insert=[]):
        Decode_Data = []
        for i in range(len(self.Fit.FuncI)):
            line_data = []
            line_data.append(self.Fit.FuncI[i])
            for j in range(3):
                line_data.append(self.Fit.Low_Boundary[i+j*len(self.Fit.FuncI)])
                line_data.append(self.Fit.Init[i+j*len(self.Fit.FuncI)])
                line_data.append(self.Fit.High_Boundary[i+j*len(self.Fit.FuncI)])
            Decode_Data.append(line_data)
        if Insert == []:   #Delete
            Decode_Data.pop()
            if Decode_Data == []:
                self.Fit.Init = []
                self.Fit.Low_Boundary = []
                self.Fit.High_Boundary = []
                self.Fit.FuncI = []
                self.Func_Delete.setEnabled(False)
                return
        elif Insert ==  1 : # UP
            row = self.Table_List[0].currentRow()
            if row > 0:
                Decode_Data[row],Decode_Data[row-1] = Decode_Data[row-1],Decode_Data[row]
        elif Insert == -1: # Down
            row = self.Table_List[0].currentRow()
            if row < len(self.Fit.FuncI)-1:
                Decode_Data[row],Decode_Data[row+1] = Decode_Data[row+1],Decode_Data[row]
        else:               #New
            Decode_Data.append(Insert)
        self.Fit.roadsetting(np.array(Decode_Data))
        self.Func_Setting_Button_Control(True)
    
    
    ##### Interaction Line #####
    #Func Setting Line
    def Func_New_Signal(self):
        self.Decode([2,0,1,10,0,1,5,1,4,6.5])
        self.Combo_Func_List.append(QComboBox())
        self.Combo_Func_List[-1].addItems(["Drude","Lorentz"])
        self.Combo_Func_List[-1].setCurrentIndex(int(self.Fit.FuncI[-1])-1)
        self.Combo_Func_List[-1].currentIndexChanged.connect(partial(self.Func_Changed_Signal,len(self.Fit.FuncI)-1))     
        if self.File_available:
                self.Fit_button.setEnabled(True)
        self.Update()
        
    def Func_Delete_Signal(self):
        self.Combo_Func_List.pop()
        self.Decode()
        if len(self.Fit.Init) == 0: # if Deleted Func were last one
            for i in range(4):
                self.Table_List[i].setRowCount(0)
            self.Fit_button.setEnabled(False)
            self.Plot_Data()
            return
        self.Update()
    def Func_Up_Signal(self):
        self.Decode(1)
        row = self.Table_List[0].currentRow()
        self.Combo_Func_List[row].setCurrentIndex(int(self.Fit.FuncI[row])-1)
        self.Combo_Func_List[row-1].setCurrentIndex(int(self.Fit.FuncI[row-1])-1)
        self.Update()
    def Func_Down_Signal(self):
        try:
            self.Decode(-1)
            row = self.Table_List[0].currentRow()
            self.Combo_Func_List[row].setCurrentIndex(int(self.Fit.FuncI[row])-1)
            self.Combo_Func_List[row+1].setCurrentIndex(int(self.Fit.FuncI[row+1])-1)
            self.Update()
        except:
            pass
    
    
    
    def Func_Changed_Signal(self,Row):
        self.Fit.FuncI[Row] = self.Combo_Func_List[Row].currentIndex()+1
        self.Plot_Setting() # Changing the Plot
        self.Table_Changer(0) # Changing the Init Table
    def Filter_Active(self):
        self.Fit.eV    = self.Fit.eV_O[(self.Fitting_Min_Value.value() < self.Fit.eV_O) * 
                                  (self.Fit.eV_O< self.Fitting_Max_Value.value())]
        self.Fit.Sigma = signal.savgol_filter(self.Fit.Sigma_O[(self.Fitting_Min_Value.value() < self.Fit.eV_O) * 
                                  (self.Fit.eV_O< self.Fitting_Max_Value.value())],
                                              self.Filter_Length.value(),
                                              self.Filter_Order.value())
        self.Weight_apply(Filter = True)
    def Fitting_changed(self):
        self.Fit.eV    = self.Fit.eV_O[(self.Fitting_Min_Value.value() < self.Fit.eV_O) * 
                                  (self.Fit.eV_O< self.Fitting_Max_Value.value())]
        self.Fit.Sigma = self.Fit.Sigma_O[(self.Fitting_Min_Value.value() < self.Fit.eV_O) * 
                                  (self.Fit.eV_O< self.Fitting_Max_Value.value())]
        self.Weight_apply(Filter = True)
        self.Plot_Setting()
        
    #Weight Func Line
    def Weight_Raw_toggled(self):
        self.Weight_Points.setEnabled(False)
        self.Weight_Rate.setEnabled(False)
    def Weight_Flat_toggled(self):
        self.Weight_Points.setEnabled(True)
        self.Weight_Rate.setEnabled(False)
    def Weight_Drude_toggled(self):
        self.Weight_Points.setEnabled(True)
        self.Weight_Rate.setEnabled(True)
    def Weight_Apply_toggled(self):
        self.Weight_apply()
    def Weight_Points_toggled(self):
        self.Data_Point = self.Weight_Points.value()
    def Weight_Rate_toggled(self):
        self.Data_Rate  = self.Weight_Rate.value()
        self.Weight_Rate_Bar.setValue(self.Weight_Rate.value())
    def Weight_Rate_Bar_toggled(self):
        self.Data_Rate  = self.Weight_Rate_Bar.value()
        self.Weight_Rate.setValue(self.Weight_Rate_Bar.value())
        
    #RT Func Line
    def RT_Value_Changed(self):
        self.Fit.RT = self.RT_Value.value()/1e6
    def RT_On_Toggled(self):
        self.Fit.RT_State = self.RT_On.isChecked()
    def Table_Changer(self,mode): # Func for Changing the Boundary Table
        self.Table_List[mode].setRowCount(len(self.Fit.FuncI))
        self.Table_List[mode].setCurrentCell(0,0)
        Drude_Num = 0
        if mode == 0:
            for i in range(len(self.Fit.FuncI)):
                Text_A  = QTableWidgetItem('{:.3f}'.format(self.Fit.Init[i],3))
                Text_Br = QTableWidgetItem('{:.3f}'.format(self.Fit.Init[i+len(self.Fit.FuncI)],3))
                Text_Xc = QTableWidgetItem('{:.3f}'.format(self.Fit.Init[i+2*len(self.Fit.FuncI)],3))
                Text_A.setTextAlignment(Qt.AlignCenter)
                Text_Br.setTextAlignment(Qt.AlignCenter)
                Text_Xc.setTextAlignment(Qt.AlignCenter)
                if self.Fit.FuncI[i] == 2:
                    self.Variable_Table.setItem(i,3,Text_Xc) # Only Lorentz has X_c Initial Value
                else:
                    Drude_Num = Drude_Num + 1
                    blink = QTableWidgetItem('')
                    blink.setFlags( Qt.ItemIsSelectable |  Qt.ItemIsEnabled )
                    self.Variable_Table.setItem(i,3,blink)
                #Setting initial value Load sequence
                self.Variable_Table.setCellWidget(i,0,self.Combo_Func_List[i])
                self.Variable_Table.setItem(i,1,Text_A) # A Initial Value
                self.Variable_Table.setItem(i,2,Text_Br) # Br Initial Value  
        else:
            for i in range(len(self.Fit.FuncI)):
                if self.Fit.FuncI[i] == 1:
                    Func = "Drude"
                    Drude_Num = Drude_Num + 1
                else:
                    Func = "Lorentz"
                Text_Func = QTableWidgetItem(Func)
                Text_Func.setFlags( Qt.ItemIsSelectable |  Qt.ItemIsEnabled )
                Text_Low    = QTableWidgetItem('{:.3f}'.format(self.Fit.Low_Boundary[i+(mode-1)*len(self.Fit.FuncI)],3))
                Text_Init   = QTableWidgetItem('{:.3f}'.format(self.Fit.Init[i+(mode-1)*len(self.Fit.FuncI)],3))
                Text_High   = QTableWidgetItem('{:.3f}'.format(self.Fit.High_Boundary[i+(mode-1)*len(self.Fit.FuncI)],3))
                Text_Low.setTextAlignment(Qt.AlignCenter)
                Text_Init.setTextAlignment(Qt.AlignCenter)
                Text_High.setTextAlignment(Qt.AlignCenter)
                self.Table_List[mode].setItem(i,0,Text_Func)
                if Func == "Drude" and mode == 3: # diable the Xc for Drude
                    for j in range(3):
                        blink = QTableWidgetItem('')
                        blink.setFlags( Qt.ItemIsSelectable |  Qt.ItemIsEnabled )
                        self.Table_List[mode].setItem(i,j+1,blink)
                    continue
                self.Table_List[mode].setItem(i,1,Text_Low)
                self.Table_List[mode].setItem(i,2,Text_Init)
                self.Table_List[mode].setItem(i,3,Text_High)
        if Drude_Num > 1 or Drude_Num == 0:
            self.RT_On.setEnabled(False)
        else:
            self.RT_On.setEnabled(True)
    def Fit_Table_Changed(self):
        # Init : 0, A :1 Br:2 xc:3
        mode = self.Fit_Table.currentIndex()
        if  mode == 4:
            self.Func_Setting_Button_Control(False)
            return
        elif mode > 0:
            self.Func_Setting_Button_Control(False)
        elif mode == 0:
            self.Func_Setting_Button_Control(True)
        self.Table_Changer(mode)


    def Cell_Entered(self):
        try:
            Table_Num = self.Fit_Table.currentIndex()
            cur  = self.Table_List[Table_Num].currentColumn()
            cur2 = self.Table_List[Table_Num].currentRow()
        except:
            print("Cell_Entered error <- Test")
        try:
            self.changedPosition = self.Table_List[Table_Num].item(cur2,cur).text()
        except:
            pass
    def Cell_changed(self):
        Table_Num = self.Fit_Table.currentIndex()
        if Table_Num == 4:
            return
        cur = self.Table_List[Table_Num].currentColumn()
        cur2 = self.Table_List[Table_Num].currentRow()
        if cur == -1 and cur2 == -1:
            return
        if cur == 0 and cur2 == 0:
            return
        if self.changedPosition != self.Table_List[Table_Num].item(cur2,cur).text():
            self.changedPosition = self.Table_List[Table_Num].item(cur2,cur).text() # preventing for overlap
            if Table_Num == 0: # Initial Table
                Value_adress = cur2+(cur-1)*len(self.Fit.FuncI)
                if float(self.Table_List[Table_Num].item(cur2,cur).text()) < float(self.Table_List[cur].item(cur2,1).text()): #Init is Lower than Minimum
                    self.Fit.Init[Value_adress] = float(self.Table_List[cur].item(cur2,1).text()) + 0.001
                elif float(self.Table_List[Table_Num].item(cur2,cur).text()) >float(self.Table_List[cur].item(cur2,3).text()): #Init is Higher than Maximum
                    self.Fit.Init[Value_adress] = float(self.Table_List[cur].item(cur2,3).text()) - 0.001
                else:
                    self.Fit.Init[(cur-1)*len(self.Fit.FuncI)+cur2] = float(self.Table_List[Table_Num].item(cur2,cur).text())
                
            else: 
                Value_adress = cur2+(Table_Num-1)*len(self.Fit.FuncI)
                if cur == 1: #Minimum Changed
                    if float(self.Table_List[Table_Num].item(cur2,cur).text())>float(self.Table_List[Table_Num].item(cur2,cur+1).text()): #Minimum is higher than Init
                        self.Fit.Low_Boundary[Value_adress] = float(self.Table_List[Table_Num].item(cur2,cur+1).text()) - 0.001
                        #QMessageBox.critical(self,'Minimum Error', 'Minimum Error')
                    else:
                        self.Fit.Low_Boundary[Value_adress] = float(self.Table_List[Table_Num].item(cur2,cur).text())
                    if self.Fit.Low_Boundary[Value_adress] >= float(self.Table_List[Table_Num].item(cur2,cur+2).text()): #Minimum is higher than Maximum
                        self.Fit.High_Boundary[Value_adress] = self.Fit.Low_Boundary[Value_adress] + 0.1
                elif cur == 2: 
                    if float(self.Table_List[Table_Num].item(cur2,cur).text()) < float(self.Table_List[Table_Num].item(cur2,cur-1).text()): #Init is Lower than Minimum
                        self.Fit.Init[Value_adress] = float(self.Table_List[Table_Num].item(cur2,cur-1).text()) + 0.001
                    elif float(self.Table_List[Table_Num].item(cur2,cur).text()) >float(self.Table_List[Table_Num].item(cur2,cur+1).text()): #Init is Higher than Maximum
                        self.Fit.Init[Value_adress] = float(self.Table_List[Table_Num].item(cur2,cur+1).text()) - 0.001
                    else:
                        self.Fit.Init[Value_adress] = float(self.Table_List[Table_Num].item(cur2,cur).text())
                elif cur == 3: #Maximum Changed
                    if float(self.Table_List[Table_Num].item(cur2,cur).text())<float(self.Table_List[Table_Num].item(cur2,cur-1).text()): #Maximum is lower than Init
                        self.Fit.High_Boundary[Value_adress] = float(self.Table_List[Table_Num].item(cur2,cur-1).text()) + 0.001
                        #QMessageBox.critical(self,'Minimum Error', 'Minimum Error')
                    else:
                        self.Fit.High_Boundary[Value_adress] = float(self.Table_List[Table_Num].item(cur2,cur).text())
                    if self.Fit.High_Boundary[Value_adress] <= float(self.Table_List[Table_Num].item(cur2,cur-2).text()): #Minimum is higher than Maximum
                        self.Fit.High_Boundary[Value_adress] = self.Fit.Low_Boundary[Value_adress] + 0.1
                
            self.Table_Changer(Table_Num)
            self.Plot_Setting()

    def Residual_Changed(self):
        self.Fit.Residual = self.Residual_Select.currentText()
    def LossFunction_Changed(self):
        self.Fit.LossFunction = self.LossFunction_Select.currentText()
    def Iterations_changed(self):
        self.MaxIterations = self.Iterations.value()
            
    ##### Menu Line #####
    def menu_bar(self):
        File_load = QAction('Import Data',self)
        File_save = QAction('Export Data',self)
        Setting_load = QAction('Import Setting',self)
        Setting_save = QAction('Export Setting',self)
        File_load.triggered.connect(self.FileLoadFunc)
        File_save.triggered.connect(self.FileSaveFunc)
        Setting_load.triggered.connect(self.SettingLoadFunc)
        Setting_save.triggered.connect(self.SettingSaveFunc)
        self.statusBar() #Maake StatusBar line
        menubar = self.menuBar()
        #Font Size
        menu = QAction()
        font = menu.font()
        font.setPointSize(16)
        menubar.setFont(font)
        #Make menu
        menubar.setNativeMenuBar(False)
        connect_menu = menubar.addMenu('&File')
        #help_menu = menubar.addMenu('&Help')
        #Add Somthing
        connect_menu.addAction(File_load)
        connect_menu.addAction(Setting_load)
        connect_menu.addAction(File_save)
        connect_menu.addAction(Setting_save)
        
        
    ###### Plot Line #####
    def Plot_Init(self):
       
        # Main Plot Line
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig) 
        self.Graph.addWidget(self.canvas)
        self.canvas.setMinimumSize(0,571)
        ax = self.fig.add_subplot(111)
        ax.set_title(self.name)
        ax.set_xlabel("eV")
        ax.set_ylabel("Sigma")
        self.fig.tight_layout(pad=0)
        self.fig.subplots_adjust(bottom=0.07)
        self.canvas.draw()
        #Residual Plot Line
        self.Residual_fig = plt.Figure()
        self.Residual_canvas = FigureCanvas(self.Residual_fig) 
        self.Residual_Graph.addWidget(self.Residual_canvas)
        self.Residual_canvas.setMinimumSize(500,100)
        self.Residual_canvas.setMaximumSize(10000,200)
        Residual_ax = self.Residual_fig.add_subplot(111)
        #Residual_ax.set_title("Residual")
        Residual_ax.set_xlabel("eV")
        Residual_ax.set_ylabel("Delta")
        #self.Residual_fig.patch.set_facecolor('none')
        #Residual_ax.axes.xaxis.set_visible(False)
        self.Residual_fig.tight_layout(pad=0)
        self.Residual_fig.subplots_adjust(bottom=0.2,top=0.9)
        self.Residual_canvas.draw()
        #Progress Plot Line
        self.Progress_fig = plt.Figure()
        self.Progress_canvas = FigureCanvas(self.Progress_fig) 
        self.Progress_Graph.addWidget(self.Progress_canvas)
        self.Progress_canvas.setMaximumSize(500,100)
        self.Progress_canvas.setMaximumSize(10000,200)
        Progress_ax = self.Progress_fig.add_subplot(111)
        Progress_ax.set_xlabel("Iterations")
        Progress_ax.set_ylabel("Cost")
        #self.Progress_fig.patch.set_facecolor('silver')
        self.Progress_fig.tight_layout(pad=0)
        self.Progress_fig.subplots_adjust(bottom=0.2,top=0.9,left=0.1)
        self.Progress_canvas.draw()
        
        
    def Plot_Data(self):
        self.fig.clear()
        self.Residual_fig.clear()
        self.Progress_fig.clear()
        ax = self.fig.add_subplot(111)
        ax.plot(self.Fit.eV,self.Fit.Sigma, 'o',markersize = 15,fillstyle='none')
        ax.set_xlim(0,self.Fit.eV[0])
        ax.set_ylim(0,np.max(self.Fit.Sigma)*1.1)
        ax.set_title(self.name)
        ax.set_xlabel("eV")
        ax.set_ylabel("Sigma")
        self.canvas.draw()
        
        Residual_ax = self.Residual_fig.add_subplot(111)
        #Residual_ax.set_title("Residual")
        #Residual_ax.set_xlabel("eV")
        Residual_ax.set_ylabel("Delta")
        self.Residual_canvas.draw()
        
        Progress_ax = self.Progress_fig.add_subplot(111)
        #Progress_ax.set_xlabel("Iterations")
        Progress_ax.set_ylabel("Cost")
        self.Progress_canvas.draw()
        
    def Plot_Progress(self):
        self.Progress_fig.clear()
        Progress_ax = self.Progress_fig.add_subplot(111)
        #Progress_ax.set_xlabel("Iterations")
        Progress_ax.set_ylabel("Cost")
        Progress_ax.plot(self.X,self.Y,linewidth = 8)
        self.Progress_canvas.draw()
    def Plot_Setting(self):
        ### Optical Conductivity Part ###
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_title(self.name)
        ax.set_xlabel("eV")
        ax.set_ylabel("Sigma")
        x = np.linspace(0,self.Fit.eV[0],num=1000)
        ax.plot(self.Fit.eV,self.Fit.Sigma,'o',markersize = 15,fillstyle='none',label='Data')
        ax.plot(x,self.Fit.Plot(self.Fit.Init,x), 'k-',linewidth = 4,label='Fitting')
        for i in range(len(self.Fit.FuncI)):
            if self.Fit.FuncI[i] == 1:
                ax.plot(x,self.Fit.Drude_Plot(self.Fit.Init[i],self.Fit.Init[i+len(self.Fit.FuncI)],self.Fit.Init[i+2*len(self.Fit.FuncI)],x),'--'
                        ,linewidth = 4,label='Drude-{}'.format(i+1))
            elif self.Fit.FuncI[i] == 2:
                ax.plot(x,self.Fit.Lorentz_Plot(self.Fit.Init[i],self.Fit.Init[i+len(self.Fit.FuncI)],self.Fit.Init[i+2*len(self.Fit.FuncI)],x),'--'
                        ,linewidth = 4,label='Lorentz-{}'.format(i+1))
        # differential term but does not match comparing data...
        
        # diff = np.diff(np.diff(self.Fit.Sigma)/np.diff(self.Fit.eV))/np.diff(self.Fit.eV[1:])
        # diff_data = diff/np.max(diff)*np.max(self.Fit.Sigma)*20+np.max(self.Fit.Sigma)/4
        # ax.plot(self.Fit.eV[:-24],diff_data[:-22])
        ax.set_xlim(0,self.Fit.eV[0])
        ax.set_ylim(0,np.max(self.Fit.Sigma)*1.1)
        ax.legend(loc = 2)
        self.canvas.draw()
        ### Residual Part ###
        self.Residual_fig.clear()
        Residual_ax = self.Residual_fig.add_subplot(111)
        #Residual_ax.set_title("Residual")
        #Residual_ax.set_xlabel("eV")
        Residual_ax.set_ylabel("Delta")
        Residual_ax.set_xlim(0,self.Fit.eV[0])
        # Cost value calculate
        if self.Fit.Residual == 'X':
            Residual_ax.plot(self.Fit.eV,self.Fit.Rasidual_X(self.Fit.Init))
        elif self.Fit.Residual == 'X^2':
            Residual_ax.plot(self.Fit.eV,self.Fit.Rasidual_X2(self.Fit.Init))
        elif self.Fit.Residual == 'Log':
            Residual_ax.plot(self.Fit.eV,self.Fit.Rasidual_Log(self.Fit.Init))
        elif self.Fit.Residual == 'Log^2':
            Residual_ax.plot(self.Fit.eV,self.Fit.Rasidual_Log2(self.Fit.Init))
        self.Residual_canvas.draw()
    def Plot_Fitting(self,W=True):
        # W = True (default) : changed the W_S value
        ### Optical Conductivity Part ###
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_title(self.name)
        ax.set_xlabel("eV")
        ax.set_ylabel("Sigma")
        x = np.linspace(0,self.Fit.eV[0],num=300)
        ax.plot(self.Fit.eV,self.Fit.Sigma,'o',markersize = 15,fillstyle='none',label='Data') # Raw Data Plot
        ax.plot(x,self.Fit.Plot(self.Fit.Init,x), 'k-',linewidth = 4,label='Fitting') # Total Fitting Data Plot
        for i in range(len(self.Fit.FuncI)):
            if self.Fit.FuncI[i] == 1:
                ax.plot(x,self.Fit.Drude_Plot(self.Fit.Init[i],self.Fit.Init[i+len(self.Fit.FuncI)],self.Fit.Init[i+2*len(self.Fit.FuncI)],x),'--'
                        ,linewidth = 4,label='Drude-{}'.format(i+1))
                # Set the W_s
                if W == True:
                    self.Variable_Table.setItem(i,4,QTableWidgetItem('{:.3f}'.format(self.Fit.Init[0*len(self.Fit.FuncI)+i])))
            elif self.Fit.FuncI[i] == 2:
                ax.plot(x,self.Fit.Lorentz_Plot(self.Fit.Init[i],self.Fit.Init[i+len(self.Fit.FuncI)],self.Fit.Init[i+2*len(self.Fit.FuncI)],x),'--'
                        ,linewidth = 4,label='Lorentz-{}'.format(i+1))
                # Set the W_s
                if W == True:
                    self.Variable_Table.setItem(i,4,QTableWidgetItem('{:.3f}'.format(self.Fit.Init[0*len(self.Fit.FuncI)+i]*self.Fit.Init[2*len(self.Fit.FuncI)+i]**2)))
        ax.set_xlim(0,self.Fit.eV[0])
        ax.set_ylim(0,np.max(self.Fit.Sigma)*1.1)
        ax.legend(loc = 2)
        self.canvas.draw()
        ### Residual Part ###
        self.Residual_fig.clear()
        Residual_ax = self.Residual_fig.add_subplot(111)
        #Residual_ax.set_title("Residual")
        #Residual_ax.set_xlabel("eV")
        Residual_ax.set_ylabel("Delta")
        Residual_ax.set_xlim(0,self.Fit.eV[0])
        # Cost value calculate
        if self.Fit.Residual == 'X':
            Residual_ax.plot(self.Fit.eV,self.Fit.Rasidual_X(self.Fit.Init))
        elif self.Fit.Residual == 'X^2':
            Residual_ax.plot(self.Fit.eV,self.Fit.Rasidual_X2(self.Fit.Init))
        elif self.Fit.Residual == 'Log':
            Residual_ax.plot(self.Fit.eV,self.Fit.Rasidual_Log(self.Fit.Init))
        elif self.Fit.Residual == 'Log^2':
            Residual_ax.plot(self.Fit.eV,self.Fit.Rasidual_Log2(self.Fit.Init))
        self.Residual_canvas.draw()
        self.Cost_Value.setText('{:.3f}'.format(self.Fit.res.cost))
        
        
    def Fit_Func(self):
        ### Optical Conductivity Part ###
        #self.Tread = Thread(target = self.Fitting_Thread)
        #self.Tread.start()
        self.Fit_button.setEnabled(False)
        self.Fit_Table.setEnabled(False)
        self.Func_New.setEnabled(False)
        self.Func_Delete.setEnabled(False)
        self.Func_Down.setEnabled(False)
        self.Func_Up.setEnabled(False)
        self.Residual_Select.setEnabled(False)
        self.LossFunction_Select.setEnabled(False)
        self.Iterations.setEnabled(False)
        self.Abort_button.setEnabled(True)
        self.X = []
        self.Y = []
        x = Fitting_Thread(self)
        x.threadEvent.connect(self.Fit_Refresh)
        x.start()
    @pyqtSlot()
    def Fit_Refresh(self):
        Num = self.MaxIterations//self.Fit.Iterations
        if self.Fitting_Count != Num and self.Fitting_stop == False:
            self.X.append(self.Fitting_Count*self.Fit_number)
            self.Y.append(self.Fit.res.cost)
            self.Plot_Progress()
            self.Plot_Fitting(W = False)
            x = Fitting_Thread(self)
            x.threadEvent.connect(self.Fit_Refresh)
            x.start()
        else: # After Fitting End
            self.X.append(self.Fitting_Count*self.Fit_number)
            self.Y.append(self.Fit.res.cost)
            self.Plot_Progress()
            self.Plot_Fitting(W = False)
            self.Update()
            self.Plot_Fitting()
            self.Fit_button.setEnabled(True)
            self.Fit_Table.setEnabled(True)
            self.Func_New.setEnabled(True)
            self.Func_Delete.setEnabled(True)
            self.Func_Down.setEnabled(True)
            self.Func_Up.setEnabled(True)
            self.Residual_Select.setEnabled(True)
            self.LossFunction_Select.setEnabled(True)
            self.Iterations.setEnabled(True)
            self.Abort_button.setEnabled(False)
            self.Fitting_stop = False
            self.Fitting_Count = 0
        
        
    def Abort_Func(self):
        self.Fitting_stop = True
        
    ##### File manager #####   
    def Weight_apply(self,Filter = False):
        if Filter == False:
            eV    = self.Fit.eV_O[(self.Fitting_Min_Value.value() < self.Fit.eV_O) * 
                                  (self.Fit.eV_O< self.Fitting_Max_Value.value())]
            Sigma = self.Fit.Sigma_O[(self.Fitting_Min_Value.value() < self.Fit.eV_O) * 
                                  (self.Fit.eV_O< self.Fitting_Max_Value.value())]
        else:
            eV    = self.Fit.eV
            Sigma = self.Fit.Sigma
        if self.Weight_Raw.isChecked():
            self.Fit.eV = eV
            self.Fit.Sigma = Sigma
        elif self.Weight_Flat.isChecked():
            x = np.linspace(eV[-1],eV[0],self.Data_Point)
            self.Fit.Sigma = interpolate.Akima1DInterpolator(eV[::-1],Sigma[::-1])(x)[::-1]
            self.Fit.eV = x[::-1]
        elif self.Weight_Drude.isChecked():
            x = np.linspace(0,1,self.Data_Point)
            x = (1-np.exp(-self.Data_Rate*x**2))*x
            x = x*(eV[0]-eV[-1])+eV[-1]
            self.Fit.Sigma = interpolate.Akima1DInterpolator(eV[::-1],Sigma[::-1])(x)[::-1]
            self.Fit.eV = x[::-1]
        self.Plot_Setting()
    
 
    def FileLoadFunc(self,drop_file = False):
        if drop_file == False:
            data = QFileDialog.getOpenFileName(self,'Open file','./Data/',"Data Files (*.txt *.mat)")
        else:
            data = drop_file
        if data[0]:
            self.name = data[0].split('/')[-1]
            try: # my style data
                self.data = np.loadtxt(data[0],skiprows=1)
                self.Fit.Sigma_O = self.data[:,1]
            except: # raw data
                self.data = np.loadtxt(data[0],skiprows=3)
                self.Fit.Sigma_O = self.data[:,2]*self.data[:,0]*self.c/60
            self.Fit.eV_O = self.data[:,0]
            if self.Fit.eV_O[0] < self.Fit.eV_O[-1]: # Data Inverse State
                self.Fit.eV_O = self.Fit.eV_O[::-1]
                self.Fit.Sigma_O = self.Fit.Sigma_O[::-1]
            self.File_available =True
            self.Weight_Box.setEnabled(True)
            self.Filter_Box.setEnabled(True)
            self.Fitting_Range_Box.setEnabled(True)
            self.Fitting_Min_Value.setRange(self.Fit.eV_O[-1],self.Fit.eV_O[0])
            self.Fitting_Min_Value.setValue(self.Fit.eV_O[-1])
            self.Fitting_Max_Value.setRange(self.Fit.eV_O[-1],self.Fit.eV_O[0])
            self.Fitting_Max_Value.setValue(self.Fit.eV_O[0])
            if self.Setting_available and self.File_available:
                self.Fit_button.setEnabled(True)
            if len(self.Fit.Init) > 0:
                self.Fit_button.setEnabled(True)
            self.Weight_apply()
            self.Plot_Setting()
        
        
    def FileSaveFunc(self):
        if self.Setting_available and self.File_available:
            data = QFileDialog.getSaveFileName(self,'Save file','./Export/',"Data Files (*.txt *.mat)")
            if data[0]:
                header = '{}\t{}\t{}'.format('eV','sigma','Fitting')
                Sum = np.vstack((self.Fit.eV, # X value
                                 self.Fit.Sigma, # Y value : Optical conductivity
                                 self.Fit.Plot(self.Fit.Init,self.Fit.eV)) # Fitting Data
                                )
                for i in range(len(self.Fit.FuncI)):
                    if self.Fit.FuncI[i] == 1:
                        Sum = np.vstack((Sum,self.Fit.Drude_Plot(self.Fit.Init[i],
                                                                 self.Fit.Init[i+len(self.Fit.FuncI)],self.Fit.Init[i+2*len(self.Fit.FuncI)],
                                                                 self.Fit.eV)))
                        header = header + '\tDrude{}'.format(i)
                    elif self.Fit.FuncI[i] == 2:
                        Sum = np.vstack((Sum,self.Fit.Lorentz_Plot(self.Fit.Init[i],
                                                                   self.Fit.Init[i+len(self.Fit.FuncI)],self.Fit.Init[i+2*len(self.Fit.FuncI)],
                                                                   self.Fit.eV)))
                        header = header + '\tLorentz{}'.format(i)
                np.savetxt(data[0],Sum.T,fmt='%.5f',delimiter='\t',header=header)
        else:
            QMessageBox.critical(self,'Export Error', 'You need Function and Data!')
            
    def SettingLoadFunc(self):
        
        
        data = QFileDialog.getOpenFileName(self,'Open file','./setting/')
        if data[0]:
            self.setting_value = np.loadtxt(data[0])
            for i in range(self.setting_value.shape[0]):
                self.Combo_Func_List.append(QComboBox())
                self.Combo_Func_List[-1].addItems(["Drude","Lorentz"])
                self.Combo_Func_List[-1].setCurrentIndex(int(self.setting_value[i][0]-1))
                self.Combo_Func_List[-1].currentIndexChanged.connect(partial(self.Func_Changed_Signal,i))       
            self.Fit.roadsetting(self.setting_value)        
            self.Setting_available = True
            self.Func_Delete.setEnabled(True)
            self.Func_Up.setEnabled(True)
            self.Func_Down.setEnabled(True)
            self.Update()
            if self.Setting_available and self.File_available:
                self.Fit_button.setEnabled(True)
                
                
    def SettingSaveFunc(self):
        if len(self.Fit.FuncI) > 0:
            data = QFileDialog.getSaveFileName(self,'Save file','./setting/',"Data Files (*.txt)")
            if data[0]:
                Save_data = []
                for i in range(len(self.Fit.FuncI)):
                    line_data = []
                    line_data.append(self.Fit.FuncI[i])
                    for j in range(3):
                        line_data.append(self.Fit.Low_Boundary[i+j*len(self.Fit.FuncI)])
                        line_data.append(self.Fit.Init[i+j*len(self.Fit.FuncI)])
                        line_data.append(self.Fit.High_Boundary[i+j*len(self.Fit.FuncI)])
                    Save_data.append(line_data)
                np.savetxt(data[0],Save_data,fmt='%.5f',delimiter='\t')
        else:
            QMessageBox.critical(self,'Export Error', 'You need Function!')
            
            
if __name__ == "__main__":
    app = QApplication(sys.argv) 
    mainWindow = MainClass()
    mainWindow.show()
    app.exec_()

        