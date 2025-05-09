# ISP_RTU
Программа предназначена для полуавтоматической отправки жалоб на отправителей спама (отправка производится на электронную почту ответственного лица которую указал пользователь). Информацию о спамерах программа получает обращаясь к электронной почте пользователя (в жалобе указываются адрес электронной почты отправителя спама, а также его ip-адрес). Обработанные письма автоматически удаляются.

# Важно
Программа распространяется под лицензией [GNU General Public License v3.0](LICENSE)

Программа НЕ фильтрует письма, жалобы отправляются на отправителей всех писем, находящихся в электронной почте пользователя. Для корректной работы необходимо создать ОТДЕЛЬНУЮ электронную почту (именно ее адрес и пароль для внешних приложений запросит программа), куда СТОРОННИМ приложением будет перенаправляться спам.

Папка [complaint_forms](complaint_forms) появится только ПОСЛЕ первого запуска приложения.

# Установка
Для установки приложения необходимо скачать файл [RTU.exe](RTU.exe) и поместить его в отдельную папку, которую программа будет использовать для своей работы. После этого установка будет завершена. Для запуска приложения используется этот же файл [RTU.exe](RTU.exe).

# Использование
При первом запуске необходимо ознакомиться с соглашением и подтвердить его. После этого необходимо перейти в раздел "Настройки", где необходимо выбрать форму для жалоб (по умолчанию [complaint_form_sample.txt](complaint_forms/complaint_form_sample.txt), возможно использовать свою форму загрузив). Также необходимо заполнить поля:
  - адрес почты (адрес электронной почты пользователя)
  - пароль для внешних приложений (пароль для внешних приложений ль электронной почты пользователя, указанной ранее)
  - адрес ответственного лица (адрес электронной почты куда необходимо отправлять жалобы)

и сохранить изменения с помощью кнопки "сохранить изменения". После этого необходимо вернутся на предыдущее окно через кнопку "Назад". В этом окне с помощью кнопки "Обработать текущие письма" можно отправить жалобы на отправителей всех писем из электронной почты пользователя. Тут же показывается краткая статистика последнего запуска (кол-во обработанных писем и кол-во отправителей спама). Выйти из программы можно по нажатию кнопки "Выйти" или с помощью крестика в правом верхнем углу окна.

# Добавление собственных форм жалоб
Файл [complaint_form_sample.txt](complaint_forms/complaint_form_sample.txt) (в папке [complaint_forms](complaint_forms)) служит образцом для создания собственных форм. В этом файле содержится несколько служебных полей:
  - <sender_email> (электронная почта пользователя)
  - <dft_email> (электронная почта отправителя спама)
  - <dft_ip> (ip-адрес отправителя спама)
В данные поля программа будет подставлять соответствующие значения. Остальной текст изменен не будет. По желанию вы можете не добавлять некоторые поля. Формат файла - .txt

# Строение проекта
  - [RTU_main.py](RTU_main.py) - основной код программы
  - [config.json](config.json) - хранение данных для работы
  - [complaint_forms](complaint_forms)/[complaint_form_sample.txt](complaint_forms/complaint_form_sample.txt) - папка для хранения форм/форма-образец
  - [RTU.exe](RTU.exe) - основной исполняемы файл

Файлы [config.json](config.json), [complaint_forms](complaint_forms), [complaint_form_sample.txt](complaint_forms/complaint_form_sample.txt) создаются при первом запуске самой программой, а также автоматически восстанавливаются в случае их удаление/повреждения.
