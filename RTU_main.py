#|ИМПОРТ БИБЛИОТЕК|#####################################################################################################
import email
import smtplib
import imaplib
import ssl
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QComboBox, QLineEdit, QMessageBox, QDialog, QDialogButtonBox, QVBoxLayout
from PyQt6.QtCore import QSize, Qt
from pathlib import Path
########################################################################################################################



#|BACK|#################################################################################################################
# Класс для imap-сервера (прием сообщений и действия с ними)
class IMAPLIB_SERVER():
    def __init__(self, login, password):
        self.imap_server = "imap.mail.ru"   # Надо
        self.login = login                  # Логин (адрес пользователя)
        self.password = password            # Пароль пользователя (для внешних приложений)

    # Постановка соединения с сервером
    def _set_server_connection(self):
        self.imap = imaplib.IMAP4_SSL(self.imap_server)
        self.imap.login(self.login, self.password)
        self.imap.select("INBOX")

    # Завершение соединения с сервером
    def _break_server_connection(self):
        self.imap.logout()

    # Получение id всех писем
    def get_emails_id(self, mode="own"):
        # Стандартный запуск (с возведением подключения к серверу)
        if mode == "raw":
            self._set_server_connection()
            result = str(self.imap.uid("search", "ALL")[1][0])[2:-1].split(' ')
            self._break_server_connection()
            return result
        # Мастер-запуск (без подключения к серверу)
        elif mode == 'own':
            return str(self.imap.uid("search", "ALL")[1][0])[2:-1].split(' ')

    # Получение адресов и ip нарушителей; формат=[adr, ip]
    def get_mail_and_id_senders(self, messages_id):
        self._set_server_connection()

        results = []
        if messages_id == ['']:
            return []
            # raise ValueError("email list is empty")
        # Перебор писем (чтобы вынуть адрес и ip)
        for email_id in messages_id:
            status, msg_data = self.imap.uid("fetch", email_id, "(RFC822)")
            if status == "OK" and msg_data != [None]:
                now_msg_data = str(dict(email.message_from_bytes(msg_data[0][1]))["Received"])

                # Берем адрес
                email_from = now_msg_data[now_msg_data.index('<')+1:now_msg_data.index('>')]
                try: ip_from = now_msg_data[now_msg_data.index('[')+1:now_msg_data.index(']')]
                except: ip_from = "None"

                # Берем ip
                if ((email_from not in [i[0] for i in results]) and (ip_from not in [j[1] for j in results])) or\
                ((email_from not in [i[0] for i in results]) and ip_from=="None"):
                    results.append((email_from, ip_from))
        self._break_server_connection()
        return results

    # Удаление писем (по списку их id)
    def delete_email(self, ids):
        result = len(ids)
        self._set_server_connection()
        for email_id in ids:
            self.imap.uid("STORE", email_id, "+FLAGS", "\\Deleted")
        self.imap.expunge()
        self._break_server_connection()
        return result

# Класс для smtp-сервера (отправка сообщений)
class SMTPLIB_SERVER():
    def __init__(self, login, password):
        self.smtp_server = "smtp.mail.ru"           # Надо
        self.context = ssl.create_default_context() # Надо
        self.smtp_port = 465                        # Надо
        self.login = login                          # Логин (адрес пользователя)
        self.password = password                    # Пароль пользователя (для внешних приложений)

    # Постановка соединения с smtp-сервером
    def _set_server_connection(self):
        self.smtp = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=self.context)
        self.smtp.login(self.login, self.password)

    # Снятие соединения с smtp-сервером
    def _break_server_connection(self):
        self.smtp.quit()

    # Отправка сообщения; аргументы=(получатель, тема, тело письма)
    def send_email(self, receiver_email, body):
        message = MIMEMultipart()
        message["From"] = self.login
        message["To"] = receiver_email
        message["Subject"] = "Жалоба на спам"
        message.attach(MIMEText(body, "plain"))

        self._set_server_connection()
        self.smtp.sendmail(self.login, receiver_email, message.as_string())
        self._break_server_connection()

# Класс курсора (Он главный)
class CURSOR():
    # Установить информацию
    def set_info(self, username, password, host, form):
        self.username = username
        self.password = password
        self.receiver_email = host
        self.form = form
        self.imap_server = IMAPLIB_SERVER(self.username, self.password)
        self.smtp_server = SMTPLIB_SERVER(self.username, self.password)

    # Генерируем тело жалобы; аргументы=(форма(путь до файла.txt), отправитель(пользователь), адрес нарушителя, ip нарушителя, причина)
    def gen_complaint(self, dft_email, dft_ip):
        with open(f"complaint_forms/{self.form}", encoding='utf-8') as file:
            complaint = ''.join(file.readlines())
            complaint = complaint.replace('<sender_email>', self.receiver_email)
            complaint = complaint.replace('<dft_email>', dft_email)
            complaint = complaint.replace('<dft_ip>', dft_ip)
            return complaint

    # Сценарий получить(id)-заблокировать-удалить
    def scenario_get_and_block_and_delete(self):
        # Проверка установил ли пользователь адрес хоста
        if self.receiver_email == None: raise ValueError("receiver_email == None")
        emails_id = self.imap_server.get_emails_id('raw')
        mail_and_id_for_block = self.imap_server.get_mail_and_id_senders(emails_id)

        # Проходимся по виновникам, и отправляем жалобу на каждого
        result_sender_amount = len(mail_and_id_for_block)
        if len(mail_and_id_for_block) == 0: return 0, 0
        for dft_mail, dft_ip in mail_and_id_for_block:
            now_complaint_msg = self.gen_complaint(dft_mail, dft_ip)
            self.smtp_server.send_email(self.receiver_email, now_complaint_msg)

        result_mails_amount = self.imap_server.delete_email(emails_id)
        return result_mails_amount, result_sender_amount
########################################################################################################################



#|FRONT|################################################################################################################
# Функция кнопки выхода
def func_quit():
    app.quit()

# Функция кнопки настроек
def func_tosettingswindow():
    window.hide_mainwindow()
    window.show_settingswindow()

# Функция кнопки назад
def func_tomainwindow():
    window.hide_settingswindow()
    window.show_mainwindow()

# Функция кнопки удаления формы
def func_delete_current_form():
    form = window.formslist_lis.currentText()
    linmast.delete_form(form)
    window.formslist_lis.clear()
    window.formslist_lis.addItems(linmast.get_info("forms_list"))

# Функция сохранения изменений
def func_save_current_changes():
    user_address = window.entermailaddress_lin.text()
    user_password = window.enterpassword_lin.text()
    host_address = window.enterhostmailaddress_lin.text()
    current_form = window.formslist_lis.currentText()
    linmast.load_info([("user_email_address", user_address),
                       ("user_email_password", user_password),
                       ("host_email_address", host_address),
                       ("current_form", current_form)])
    linmast.check_is_all_data_exist()
    window.currentform_lab.setText(f"Текущая форма: {current_form}")

# Функция обработки почты
def func_process_mail():
    work_result = cursor.scenario_get_and_block_and_delete()
    window.amountmails_lab.clear()
    window.amountadresses_lab.clear()
    window.amountmails_lab.setText(f"Писем обработано {work_result[0]}")
    window.amountadresses_lab.setText(f"Адресов обработано {work_result[1]}")

# Класс пользовательского соглашения
class UserAgreementDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Пользовательское соглашение")
        Qbtns = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.buttonBox = QDialogButtonBox(Qbtns)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel("Для работы приложению необходимо передать информацию о:\n"
                         "\t-вашем адресе электронной почты*\n"
                         "\t-пароле для внешних приложений (от вашей электронной почты)\n"
                         "\t-почтовый адрес ответственного лица\n\n"
                         "Подтверждая пользовательское соглашение и/или продолжая работу с приложением,\nвы подтверждаете"
                         " свое согласие на обработку указанных выше данных.\nОни будут использованы лишь для корректной"
                         " работы приложения.\nДальнейшее распространение данной информации не предусмотренно.\n\n"
                         "*Необходимо создать отдельную электронную почту, куда будет перенаправлен спам\n(сторонним"
                         " приложением, на ваше усмотрение),\nтолько в этом случае приложение будет корректно работать"
                         " и не получит доступа к вашим личным письмам.")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

# Класс окна
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mainwindow_widgets = []   # Список виджетов главного раздела
        self.settings_widgets = []  # Список виджетов раздела настроек
        if not linmast.get_info("is_user_know_agreement"): self.user_agreement()

    # Функция главного раздела
    def mainwindow(self):
        # Параметры главного окна
        self.setWindowTitle("RTU")
        self.setFixedSize(QSize(600, 380))

        # Надпись главного меню
        self.mainmenu_label = QLabel(self)
        self.mainwindow_widgets.append(self.mainmenu_label)
        self.mainmenu_label.setFixedSize(592, 50)
        self.mainmenu_label.move(4, 4)
        self.mainmenu_label.setText("Главное меню")
        self.mainmenu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mainmenu_label.setStyleSheet("border: 1px solid gray; background-color: gray; font-size: 32px")

        # Левая половина
        self.left_half_back = QLabel(self)
        self.mainwindow_widgets.append(self.left_half_back)
        # self.left_half_back.setObjectName("half") # Для дальнейшей стилизации
        self.left_half_back.setFixedSize(294, 318)
        self.left_half_back.move(4, 58)

        # Л надпись результатов
        self.results_lab = QLabel(self)
        self.mainwindow_widgets.append(self.results_lab)
        self.results_lab.setFixedSize(286, 50)
        self.results_lab.move(8, 62)
        self.results_lab.setText("Результаты последней обработки:")
        self.results_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_lab.setStyleSheet("background-color: white")

        # Л надпись 1 (писем)
        self.amountmails_lab = QLabel(self)
        self.mainwindow_widgets.append(self.amountmails_lab)
        self.amountmails_lab.setFixedSize(286, 50)
        self.amountmails_lab.move(8, 114)
        self.amountmails_lab.setText("Писем обработано 0")
        self.amountmails_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Л надпись 2 (отправителей)
        self.amountadresses_lab = QLabel(self)
        self.mainwindow_widgets.append(self.amountadresses_lab)
        self.amountadresses_lab.setFixedSize(286, 50)
        self.amountadresses_lab.move(8, 168)
        self.amountadresses_lab.setText("Адресов обработано 0")
        self.amountadresses_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Правая половина
        self.right_half_back = QLabel(self)
        self.mainwindow_widgets.append(self.right_half_back)
        # self.right_half_back.setObjectName("half")
        self.right_half_back.setFixedSize(294, 318)
        self.right_half_back.move(302, 58)

        # П кнопка обработки
        self.process_but = QPushButton(self)
        self.mainwindow_widgets.append(self.process_but)
        self.process_but.setFixedSize(286, 100)
        self.process_but.move(306, 62)
        self.process_but.setText("Обработать текущие письма")
        self.process_but.clicked.connect(func_process_mail)

        flag = linmast.get_info("is_all_info_exist")
        if flag == 0: self.process_but.setEnabled(False)
        else: self.process_but.setEnabled(True)

        # П инфо надпись
        flag = linmast.get_info("is_all_info_exist")
        if flag == 0:
            self.infoaboutsettings_lab = QLabel(self)
            self.mainwindow_widgets.append(self.infoaboutsettings_lab)
            self.infoaboutsettings_lab.setFixedSize(286, 40)
            self.infoaboutsettings_lab.move(306, 120)
            self.infoaboutsettings_lab.setText("Сначала необходимо заполнить все данные в разделе <<Настройки>>")
            self.infoaboutsettings_lab.setWordWrap(True)
            self.infoaboutsettings_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # П кнопка настроек
        self.tosettings_but = QPushButton(self)
        self.mainwindow_widgets.append(self.tosettings_but)
        self.tosettings_but.setFixedSize(286, 100)
        self.tosettings_but.move(306, 166)
        self.tosettings_but.setText("Настройки")
        self.tosettings_but.clicked.connect(func_tosettingswindow)
        self.tosettings_but.setEnabled(True)

        # П кнопка выхода
        self.quit_but = QPushButton(self)
        self.mainwindow_widgets.append(self.quit_but)
        self.quit_but.setFixedSize(286, 100)
        self.quit_but.move(306, 270)
        self.quit_but.setText("Выйти")
        self.quit_but.clicked.connect(func_quit)
        self.quit_but.setEnabled(True)

        # Запуск
        for widget in self.mainwindow_widgets:
            widget.show()
        self.show()

    # Функция появления главного окна
    def show_mainwindow(self):
        self.setWindowTitle("RTU")
        self.setFixedSize(QSize(600, 380))
        if self.mainwindow_widgets == []: self.mainwindow()
        else:
            for widget in self.mainwindow_widgets:
                widget.show()

    # Функция сокрытия главного раздела
    def hide_mainwindow(self):
        for widget in self.mainwindow_widgets:
            widget.hide()


    # Функция окна настроек
    def settingswindow(self):
        self.setWindowTitle("RTU")
        self.setFixedSize(QSize(600, 295))

        # Надпись настройки
        self.settings_lab = QLabel(self)
        self.settings_widgets.append(self.settings_lab)
        self.settings_lab.setFixedSize(507, 50)
        self.settings_lab.move(4, 4)
        self.settings_lab.setText("Настройки")
        self.settings_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.settings_lab.setStyleSheet("background-color: gray;")

        # Кнопка назад
        self.tomainmenu_but = QPushButton(self)
        self.settings_widgets.append(self.tomainmenu_but)
        self.tomainmenu_but.setFixedSize(80, 50)
        self.tomainmenu_but.move(516, 4)
        self.tomainmenu_but.setText("Назад")
        self.tomainmenu_but.clicked.connect(func_tomainwindow)
        self.tomainmenu_but.setEnabled(True)

        # Надпись формы жалоб
        self.complaintform_lab = QLabel(self)
        self.settings_widgets.append(self.complaintform_lab)
        self.complaintform_lab.setFixedSize(292, 40)
        self.complaintform_lab.move(4, 58)
        self.complaintform_lab.setText("Формы жалоб")
        self.complaintform_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Надпись текущая форма
        self.currentform_lab = QLabel(self)
        self.settings_widgets.append(self.currentform_lab)
        self.currentform_lab.setFixedSize(292, 30)
        self.currentform_lab.move(4, 95)
        current_form = linmast.get_info("current_form")
        if current_form == "None": self.currentform_lab.setText("Текущая форма: не выбрана")
        else: self.currentform_lab.setText(f"Текущая форма: {current_form}")
        self.currentform_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Выпадающий список
        self.formslist_lis = QComboBox(self)
        self.settings_widgets.append(self.formslist_lis)
        self.formslist_lis.addItems(linmast.get_info("forms_list"))
        self.formslist_lis.setFixedSize(292, 25)
        self.formslist_lis.move(4, 129)

        # Кнопка удалить текущую форму
        self.deletecurrentform_button = QPushButton(self)
        self.settings_widgets.append(self.deletecurrentform_button)
        self.deletecurrentform_button.setFixedSize(292, 50)
        self.deletecurrentform_button.move(4, 158)
        self.deletecurrentform_button.setText("Удалить текущую форму")
        self.deletecurrentform_button.clicked.connect(func_delete_current_form)
        self.deletecurrentform_button.setEnabled(True)

        # Надпись о добавлении формы
        self.addform_lab = QLabel(self)
        self.settings_widgets.append(self.addform_lab)
        self.addform_lab.setFixedSize(292, 79)
        self.addform_lab.move(4, 212)
        self.addform_lab.setText("Для добавления новой формы, перенесите файл .txt в папку complaint_froms.\n"
                                 "Обратите внимание что формат полей информации должен соответствовать "
                                 "формату в форме complaint_form_sample.txt")
        self.addform_lab.setWordWrap(True)

        # Надпись настройки почты
        self.mailsettings_lab = QLabel(self)
        self.settings_widgets.append(self.mailsettings_lab)
        self.mailsettings_lab.setFixedSize(292, 40)
        self.mailsettings_lab.move(304, 58)
        self.mailsettings_lab.setText("Настройки почты")
        self.mailsettings_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Надпись адрес почты
        self.mailaddress_lab = QLabel(self)
        self.settings_widgets.append(self.mailaddress_lab)
        self.mailaddress_lab.setFixedSize(292, 15)
        self.mailaddress_lab.move(304, 102)
        self.mailaddress_lab.setText("адрес почты")
        self.mailaddress_lab.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Ввод адрес почты
        self.entermailaddress_lin = QLineEdit(self)
        self.settings_widgets.append(self.entermailaddress_lin)
        self.entermailaddress_lin.setFixedSize(292, 20)
        self.entermailaddress_lin.move(304, 121)
        user_mail_address = linmast.get_info("user_email_address")
        if user_mail_address != "None": self.entermailaddress_lin.setText(user_mail_address)
        self.entermailaddress_lin.setPlaceholderText("example@mail.ru")

        # Надпись пароль
        self.changepassword_lab = QLabel(self)
        self.settings_widgets.append(self.changepassword_lab)
        self.changepassword_lab.setFixedSize(292, 15)
        self.changepassword_lab.move(304, 149)
        self.changepassword_lab.setText("пароль (для внешних приложений)")
        self.changepassword_lab.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Ввод пароль
        self.enterpassword_lin = QLineEdit(self)
        self.settings_widgets.append(self.enterpassword_lin)
        self.enterpassword_lin.setFixedSize(292, 20)
        self.enterpassword_lin.move(304, 168)
        user_mail_password = linmast.get_info("user_email_password")
        if user_mail_password != "None": self.enterpassword_lin.setText(user_mail_password)
        self.enterpassword_lin.setPlaceholderText("exampleexampleexample")

        # Надпись адрес ответственного лица
        self.hostmailaddress_lab = QLabel(self)
        self.settings_widgets.append(self.hostmailaddress_lab)
        self.hostmailaddress_lab.setFixedSize(292, 15)
        self.hostmailaddress_lab.move(304, 193)
        self.hostmailaddress_lab.setText("адрес ответственного лица (администратор сети, ...)")
        self.hostmailaddress_lab.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Ввод адрес ответственного лица
        self.enterhostmailaddress_lin = QLineEdit(self)
        self.settings_widgets.append(self.enterhostmailaddress_lin)
        self.enterhostmailaddress_lin.setFixedSize(292, 20)
        self.enterhostmailaddress_lin.move(304, 213)
        host_mail_address = linmast.get_info("host_email_address")
        if host_mail_address != "None": self.enterhostmailaddress_lin.setText(host_mail_address)
        self.enterhostmailaddress_lin.setPlaceholderText("example@mail.ru")

        # Кнопка сохранить изменения
        self.savechanges_but = QPushButton(self)
        self.settings_widgets.append(self.savechanges_but)
        self.savechanges_but.setFixedSize(292, 50)
        self.savechanges_but.move(304, 241)
        self.savechanges_but.setText("Сохранить изменения")
        self.savechanges_but.clicked.connect(func_save_current_changes)
        self.savechanges_but.setEnabled(True)

        # Запуск
        for widget in self.settings_widgets:
            widget.show()
        self.show()

    # Функция появления окна настроек
    def show_settingswindow(self):
        self.setWindowTitle("RTU")
        self.setFixedSize(QSize(600, 295))
        if self.settings_widgets == []: self.settingswindow()
        else:
            for widget in self.settings_widgets:
                widget.show()

    # Функция сокрытия окна настроек
    def hide_settingswindow(self):
        for widget in self.settings_widgets:
            widget.hide()

    # Функция для пользовательского соглашения
    def user_agreement(self):
        dlg = UserAgreementDialog()
        if dlg.exec():
            linmast.load_info([("is_user_know_agreement", 1)])
        else:
            raise SystemError("Для дальнейшей работы необходимо подтвердить пользовательское соглашение")
########################################################################################################################



#|СВЯЗКА|###############################################################################################################
class link_master():
    def __init__(self):
        # Восстановление json в случае повреждения/отсутствия
        self.standart_data = {
            "is_all_info_exist": 0,
            "is_user_know_agreement": 0,
            "user_email_address": "None",
            "user_email_password": "None",
            "host_email_address": "None",
            "current_form": "None",
            "forms_list": []
        }
        if os.path.isfile("config.json"):
            if open("config.json").readlines() == []:
                with open("config.json", 'w') as file:
                    json.dump(self.standart_data, file, indent=4)
            try:
                json.load(open("config.json"))
            except:
                with open("config.json", 'w') as file:
                    json.dump(self.standart_data, file, indent=4)
        else:
            with open("config.json", 'w') as file:
                json.dump(self.standart_data, file, indent=4)

        # Восстановление папки с формами в случае повреждения/отсутствия
        self.standat_form_text = "Жалоба\nОтправитель: <sender_email>\nОбвиняемый: адрес - <dft_email>; ip - <dft_ip>"
        if not os.path.isdir("complaint_forms"):
            os.mkdir("complaint_forms")
            with open("complaint_forms/complaint_form_sample.txt", "w", encoding="utf-8") as file:
                file.write(self.standat_form_text)
        else:
            try:
                with open("complaint_forms/complaint_form_sample.txt", "r", encoding="utf-8") as file:
                    now = ''.join(file.readlines())
                if now != self.standat_form_text:
                    with open("complaint_forms/complaint_form_sample.txt", "w", encoding="utf-8") as file:
                        file.write(self.standat_form_text)
            except:
                with open("complaint_forms/complaint_form_sample.txt", "w", encoding="utf-8") as file:
                    file.write(self.standat_form_text)

        # Обновления списка файлов
        self.update_file_list()

    # Попытка установить данные для курсора (если они есть)
    def try_set_data_for_cursor(self):
        if self.get_info("is_all_info_exist") == 1:
            username = linmast.get_info("user_email_address")
            password = linmast.get_info("user_email_password")
            host = linmast.get_info("host_email_address")
            form = linmast.get_info("current_form")
            cursor.set_info(username, password, host, form)

    # Поиск форм и обновление списка
    def update_file_list(self):
        forms_list = []
        for file in os.listdir("complaint_forms"):
            if '.txt' in file: forms_list.append(file)
        self.load_info([("forms_list", forms_list)])

    # Получение информации всей/конкретной
    def get_info(self, info_type="all"):
        if info_type == "all":
            with open("config.json") as file:
                results = dict(json.load(file))
        else:
            with open("config.json") as file:
                results = dict(json.load(file))[info_type]
        return results

    # Загрузка информации
    def load_info(self, info, info_type="all"):
        with open("config.json") as file:
            data = dict(json.load(file))
            for elem in info:
                data[elem[0]] = elem[1]
        with open("config.json", 'w') as file:
            json.dump(data, file, indent=4)

    # Удаление формы и обновление списка
    def delete_form(self, form):
        if form != "complaint_form_sample.txt":
            os.remove(f"complaint_forms/{form}")
            self.update_file_list()

    # Проверка все ли данные введены
    def check_is_all_data_exist(self):
        data = str(self.get_info())
        if ("None" not in data) and ('[]' not in data):
            username = linmast.get_info("user_email_address")
            password = linmast.get_info("user_email_password")
            host = linmast.get_info("host_email_address")
            form = linmast.get_info("current_form")
            cursor.set_info(username, password, host, form)
            if self.get_info("is_all_info_exist") != 1:
                window.infoaboutsettings_lab.destroy()
                window.mainwindow_widgets.remove(window.infoaboutsettings_lab)
            window.process_but.setEnabled(True)
            self.load_info([("is_all_info_exist", 1)])
########################################################################################################################



#|ЗАПУСК|###############################################################################################################
if __name__ == "__main__":
    cursor = CURSOR()
    linmast = link_master()
    linmast.try_set_data_for_cursor()

    app = QApplication(sys.argv)
    # app.setStyleSheet(Path("fragments_design.qss").read_text())
    window = MainWindow()

    window.show_mainwindow()
    app.exec()
########################################################################################################################