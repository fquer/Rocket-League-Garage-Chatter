from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import winsound
from bs4 import BeautifulSoup
import os
from msedge.selenium_tools import Edge, EdgeOptions
from time import sleep
import subprocess

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

class Worker(QObject):
    
    text = pyqtSignal(str,int)
    sifirla = pyqtSignal()
    customers = pyqtSignal(list)
    text_sender = pyqtSignal(str)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)

        file = open('account.txt','r')
        account = file.read()
        file.close()

        account = account.split('\n')

        self.email = account[0]
        self.password = account[1]

        self.customer_list = []

        self.message_list = []
        self.message_list_old = []
        self.message_list_getted = []
        self.message_list_getted_old = []

        

    def do_work(self):
        
        options = EdgeOptions()
        options.use_chromium = True
        #options.add_argument('--headless')
        options.add_argument("--mute-audio")
        self.driver = Edge("msedgedriver.exe",options=options)
        self.driver.set_window_size(1920, 1080)

        # Siteye login olma
        self.driver.get("https://rocket-league.com/login")
        self.driver.find_element_by_id("acceptPrivacyPolicy").click()
        self.driver.find_element_by_name("email").send_keys(self.email)
        self.driver.find_element_by_name("password").send_keys(self.password)
        self.driver.find_element_by_name("submit").click()
        # Login olundu

        # Chat'e git verileri cek
        self.driver.get("https://rocket-league.com/chat")
        source = BeautifulSoup(self.driver.page_source,"lxml")
        # Veriler cekildi

        sleep(1)

        # Mesaj listesini combobox'a yollama
        self.customer_list.clear()
        self.customer = str(source.find('div', {"class": "rlg-chat__name"})).split('<span>')[1].replace('</span>\n</div>','')
        self.customer_list.append(self.customer)
        self.next_customer = self.customer

        for j in source.find_all('a', {"class": "rlg-chat__thread --is-user --not-archived"}):
            self.customer_list.append(str(j['href']).split('/chat/')[1].strip())
        
        self.customers.emit(self.customer_list)
        # Yollandi

        first = True
        first_message = True
        
        while True:
            sleep(0.4) # CPU yuku azaltma
            source_old = source
            source = BeautifulSoup(self.driver.page_source,"lxml")
            
            # Listedeki secili isim suanki isimle esit degil ise
            if self.customer.strip() != self.next_customer.strip():

                self.driver.get("https://rocket-league.com/chat/{}".format(self.next_customer)) # Secili olan kullanici chat'ine git
                source = BeautifulSoup(self.driver.page_source,"lxml")
                self.customer = self.next_customer.strip() # Artik suanki musterimiz sonraki musterimiz oldu bir dahaki kontrolde buraya girmeyecektir.

                first_message = True
            
            if source.find('a', {'class': 'rlg-chat__thread --new'}) != None or source.find('a', {'class': 'rlg-chat__thread --is-user --new --not-archived'}) != None: # Eger yeni mesaj var ise

                source = BeautifulSoup(self.driver.page_source,"lxml")
                self.customer_list.clear()
                        
                for k in source.find_all('a', {"class": "rlg-chat__thread"}): # Oncelikle yeni musteri listesini atiyoruz

                    self.customer_list.append(str(k['href']).split('/chat/')[1].strip())

                # Yeni mesaj var ise
                for j in source.find_all('a', {'class': 'rlg-chat__thread --new'}): # Daha sonrasinda da yeni mesaji kim yollamis ona bakiyoruz
                    if j != "":
                    
                        new_messager = str(j['href']).split('/chat/')[1].strip() # Yeni mesaji yollayan kisi
                        say = 0
                        for chat_customer in self.customer_list: # For dongusunde o kisiyi bulup yanina yeni mesaj olduguna dair ibare birakiyoruz
                            if chat_customer == new_messager:
                                self.customer_list[say] = new_messager + "   [ New Message ]"
                            say+=1

                # Yeni mesaj var ise
                for j in source.find_all('a', {'class': 'rlg-chat__thread --is-user --new --not-archived'}): # Daha sonrasinda da yeni mesaji kim yollamis ona bakiyoruz
                    if j != "":
                    
                        new_messager = str(j['href']).split('/chat/')[1].strip() # Yeni mesaji yollayan kisi
                        say = 0
                        for chat_customer in self.customer_list: # For dongusunde o kisiyi bulup yanina yeni mesaj olduguna dair ibare birakiyoruz
                            if chat_customer == new_messager:
                                self.customer_list[say] = new_messager + "   [ New Message ]"
                            say+=1

                self.customers.emit(self.customer_list)
                # Yollandi

                winsound.PlaySound('new_message_another.wav', winsound.SND_FILENAME)
                first_message = True

            else:
                # Yeni musteri listeisini yollama
                self.customer_list.clear()

                for k in source.find_all('a', {"class": "rlg-chat__thread"}):

                    self.customer_list.append(str(k['href']).split('/chat/')[1].strip())
                
                self.customers.emit(self.customer_list)
                # Yollandi
                

            self.message_list_old.clear()
            self.message_list_getted_old.clear()
            for i in source_old.find_all('div', {"class": [ "rlg-chat__message --self",
                                                        "rlg-chat__message --has-avatar --self",
                                                        "rlg-chat__message --has-avatar",
                                                        "rlg-chat__message"]}): # mesajlari cekme
                message = str(i.text.strip().split('\n')[0]).strip()
                if str(i).strip().find('--self') == -1:
                    self.message_list_getted_old.append(message)
                self.message_list_old.append(message)
                

            self.message_list.clear()
            self.message_list_getted.clear()
            for i in source.find_all('div', {"class": [ "rlg-chat__message --self",
                                                        "rlg-chat__message --has-avatar --self",
                                                        "rlg-chat__message --has-avatar",
                                                        "rlg-chat__message"]}): # mesajlari cekme
                message = str(i.text.strip().split('\n')[0]).strip()
                if str(i).strip().find('--self') == -1:
                    self.message_list_getted.append(message)
                self.message_list.append(message)

            if self.message_list_getted != self.message_list_getted_old and first_message == False:
                winsound.PlaySound('new_message_current.wav', winsound.SND_FILENAME)

            if self.message_list_old != self.message_list or first == True:
                
                first = False
                first_message = False
                self.sifirla.emit() # Chat ekranini temizler

                # Mesaj yazdirma baslangici
                self.customer = source.find('span', {'class': 'rlg-chat__convotitle'}).text.split('Chat with ')[1]
                self.text_sender.emit(self.customer) # son gonderen ad yazma

                for i in source.find_all('div', {"class": [ "rlg-chat__message --self",
                                                            "rlg-chat__message --has-avatar --self",
                                                            "rlg-chat__message --has-avatar",
                                                            "rlg-chat__message"]}): # mesajlari cekme
                    message = str(i.text.strip().split('\n')[0]).strip()
                    if str(i).strip().find('--self') != -1: # Mesajlar bana aitse saga yapistir degil ise sola yapistir. Sag = 1
                        self.text.emit(message,1)

                    else:
                        self.text.emit(message,0)
                
                # Mesaj yazdirma bitisi

    def send_message(self,message):
        self.driver.find_element_by_id('messagetext').send_keys(message)
        self.driver.find_element_by_id('user-message-send-reply').click()

    def change_customer(self,customer):
        self.next_customer = customer

class Ui_MainWindow(QtWidgets.QWidget):
    stop_signal = pyqtSignal()
    
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setFixedSize(750, 520)
        MainWindow.setStyleSheet("background-color: rgb(67, 67, 67);")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        font = QtGui.QFont()
        font.setPointSize(11)
        
        self.label_chat = QtWidgets.QLabel(self.centralwidget)
        self.label_chat.setGeometry(QtCore.QRect(50, 10, 250, 30))
        self.label_chat.setStyleSheet("background-color: rgb(202, 202, 202);")
        self.label_chat.setObjectName("label_chat")
        self.label_chat.setFont(font)

        self.tb_chat = QtWidgets.QTextBrowser(self.centralwidget)
        self.tb_chat.setGeometry(QtCore.QRect(50, 50, 400, 380))
        self.tb_chat.setStyleSheet("background-color: rgb(202, 202, 202);")
        self.tb_chat.setObjectName("tb_chat")
        self.tb_chat.setFont(font)
        self.tb_chat.setText("Loading...")

        self.chat_text_input = QtWidgets.QLineEdit(self.centralwidget)
        self.chat_text_input.setGeometry(QtCore.QRect(50, 450, 320, 30))
        self.chat_text_input.setStyleSheet("background-color: rgb(202, 202, 202);")
        self.chat_text_input.setObjectName("chat_text_input")
        self.chat_text_input.installEventFilter(self)
        self.chat_text_input.setFont(font)

        self.chat_send_button = QtWidgets.QPushButton(self.centralwidget)
        self.chat_send_button.setGeometry(QtCore.QRect(380, 450, 70, 30))
        self.chat_send_button.setStyleSheet("background-color: rgb(202, 202, 202);")
        self.chat_send_button.setObjectName("chat_send_button")
        self.chat_send_button.setText("Send")
        self.chat_send_button.clicked.connect(self.chat_send)

        self.chat_customers = QtWidgets.QListWidget(self.centralwidget)
        self.chat_customers.setGeometry(QtCore.QRect(480, 50, 250, 380))
        self.chat_customers.setStyleSheet("background-color: rgb(202, 202, 202);")
        self.chat_customers.setObjectName("chat_customers")
        self.chat_customers.currentItemChanged.connect(self.customerOnChanged)
        self.chat_customers.setFont(font)

        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        self.worker.text.connect(self.monitor_chat)
        self.worker.text_sender.connect(self.set_chat_title)
        self.worker.sifirla.connect(self.new_message)
        self.worker.customers.connect(self.add_customer)

        self.thread.started.connect(self.worker.do_work)       
        self.thread.start()
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        MainWindow.setWindowTitle("Rocket League Trade Chatter")
        MainWindow.show()

    def monitor_chat(self,text,side):
        self.tb_chat.append(text)
        if side == 1:
            self.tb_chat.setAlignment(QtCore.Qt.AlignRight)

        else:
            self.tb_chat.setAlignment(QtCore.Qt.AlignLeft)
    
    def chat_send(self):
        self.worker.send_message(self.chat_text_input.text())
        self.chat_text_input.setText("")

    def set_chat_title(self,title):
        self.label_chat.setText("  "+title)

    def add_customer(self,customers):
        self.chat_customers.clear()
        for i in customers:
            self.chat_customers.addItem(i)

    def customerOnChanged(self):
        if self.chat_customers.currentItem() != None:
            self.worker.change_customer(self.chat_customers.currentItem().text().split('[ New Message ]')[0])
        
    def new_message(self):
        self.tb_chat.setText("")

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and obj is self.chat_text_input:
            if event.key() == QtCore.Qt.Key_Enter or event.key() == QtCore.Qt.Key_Return and self.chat_text_input.hasFocus():
                self.chat_send()
        return super().eventFilter(obj, event)


class MyWindow(QtWidgets.QMainWindow):
    def closeEvent(self,event):
        subprocess.call('taskkill /f /im msedgedriver.exe')
        subprocess.call('taskkill /f /im msedge.exe')


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MyWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    sys.exit(app.exec_())