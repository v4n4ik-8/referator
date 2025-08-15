from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QSpinBox, 
                           QPushButton, QTextEdit, QProgressBar, QMessageBox,
                           QScrollArea, QFrame, QFileDialog, QLineEdit,
                           QComboBox, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from controllers.essay_generator import EssayGeneratorController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = EssayGeneratorController()
        self.initUI()
        self.connectSignals()
        self.completed_essays = []  # Список готовых рефератов

    def calculate_pages(self) -> float:
        """Рассчитывает примерное количество страниц"""
        # ~1800 символов на страницу (TNR 14, обычный интервал)
        chars_per_page = 1800
        total_chars = (
            self.symbols_spin.value() * self.chapters_spin.value() +  # главы
            2000  # введение (~2000 символов)
        )
        return round(total_chars / chars_per_page, 1)

    def update_pages_label(self):
        """Обновляет информацию о количестве страниц"""
        pages = self.calculate_pages()
        self.pages_label.setText(f"Примерно страниц: {pages}")

    def initUI(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle('Рефератор')
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создаем скроллируемую область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Секция ввода тем
        topics_group = QFrame()
        topics_group.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        topics_layout = QVBoxLayout(topics_group)
        
        topics_label = QLabel("Темы рефератов (каждая тема с новой строки):")
        self.topics_input = QTextEdit()
        self.topics_input.setPlaceholderText("Введите темы рефератов...")
        topics_layout.addWidget(topics_label)
        topics_layout.addWidget(self.topics_input)

        # Добавляем кнопку очистки для тем
        topics_buttons_layout = QHBoxLayout()
        self.clear_topics_button = QPushButton("Очистить темы")
        self.clear_topics_button.clicked.connect(self.topics_input.clear)
        topics_buttons_layout.addStretch()
        topics_buttons_layout.addWidget(self.clear_topics_button)
        topics_layout.addLayout(topics_buttons_layout)

        # Настройки генерации
        settings_group = QFrame()
        settings_group.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        settings_layout = QVBoxLayout(settings_group)
        
        # Добавляем выбор языка
        language_layout = QHBoxLayout()
        language_label = QLabel("Язык реферата:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Русский", "English", "Українська", "Беларуская"])
        self.language_combo.setCurrentText("Русский")
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()

        # Путь сохранения
        path_layout = QHBoxLayout()
        path_label = QLabel("Путь сохранения:")
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Выберите папку для сохранения рефератов...")
        self.path_button = QPushButton("Обзор...")
        self.path_button.clicked.connect(self.choose_path)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.path_button)
        
        # Количество глав
        chapters_layout = QHBoxLayout()
        chapters_label = QLabel("Количество глав:")
        self.chapters_spin = QSpinBox()
        self.chapters_spin.setRange(3, 10)
        self.chapters_spin.setValue(5)
        self.chapters_spin.valueChanged.connect(self.update_pages_label)
        chapters_layout.addWidget(chapters_label)
        chapters_layout.addWidget(self.chapters_spin)
        chapters_layout.addStretch()
        
        # Количество символов на главу
        symbols_layout = QHBoxLayout()
        symbols_label = QLabel("Символов на главу:")
        self.symbols_spin = QSpinBox()
        self.symbols_spin.setRange(1000, 10000)
        self.symbols_spin.setValue(2000)
        self.symbols_spin.setSingleStep(500)
        self.symbols_spin.valueChanged.connect(self.update_pages_label)
        symbols_layout.addWidget(symbols_label)
        symbols_layout.addWidget(self.symbols_spin)
        symbols_layout.addStretch()

        # Добавляем метку с количеством страниц
        pages_layout = QHBoxLayout()
        self.pages_label = QLabel()
        pages_layout.addWidget(self.pages_label)
        pages_layout.addStretch()
        self.update_pages_label()  # Инициализируем значение

        # Обновляем settings_layout
        settings_layout.addLayout(language_layout)
        settings_layout.addLayout(path_layout)
        settings_layout.addLayout(chapters_layout)
        settings_layout.addLayout(symbols_layout)
        settings_layout.addLayout(pages_layout)

        # Добавляем группы в скроллируемую область
        scroll_layout.addWidget(topics_group)
        scroll_layout.addWidget(settings_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Статус готовых рефератов
        self.completed_label = QLabel("")
        layout.addWidget(self.completed_label)

        # Прогресс бар и статус
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Готов к генерации")
        self.cancel_button = QPushButton("Отменить")
        self.cancel_button.clicked.connect(self.cancel_generation)
        self.cancel_button.setEnabled(False)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.cancel_button)
        layout.addLayout(progress_layout)
        layout.addWidget(self.status_label)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)  # Устанавливаем отступ между элементами
        buttons_layout.setContentsMargins(10, 0, 10, 0)  # Отступы слева и справа
        
        # Создаем контейнер для кнопки генерации
        generate_container = QWidget()
        generate_layout = QHBoxLayout(generate_container)
        generate_layout.setContentsMargins(0, 0, 0, 0)  # Убираем внутренние отступы контейнера
        self.generate_button = QPushButton("Сгенерировать")
        self.generate_button.clicked.connect(self.start_generation)
        generate_layout.addWidget(self.generate_button)
        
        # Создаем контейнер для кнопок поддержки
        support_container = QWidget()
        support_layout = QHBoxLayout(support_container)
        support_layout.setSpacing(10)  # Отступ между кнопками поддержки
        support_layout.setContentsMargins(0, 0, 0, 0)  # Убираем внутренние отступы контейнера
        
        self.donate_button = QPushButton("Поддержать проект")
        self.donate_button.clicked.connect(self.show_donate_info)
        
        self.telegram_button = QPushButton("Скинуть сиськи разработчику")
        self.telegram_button.clicked.connect(self.open_telegram)
        
        support_layout.addWidget(self.donate_button)
        support_layout.addWidget(self.telegram_button)
        
        # Устанавливаем фиксированные размеры для контейнеров
        total_width = self.width()
        button_spacing = 20  # Отступ между кнопками
        margins = 40  # Сумма левого и правого отступов
        available_width = total_width - margins - (2 * button_spacing)  # Доступная ширина с учетом отступов
        
        generate_width = int(available_width * 0.5)  # 50% от доступной ширины
        support_width = int(available_width * 0.25)  # 25% от доступной ширины для каждой кнопки поддержки
        
        generate_container.setFixedWidth(generate_width)
        self.donate_button.setFixedWidth(support_width)
        self.telegram_button.setFixedWidth(support_width)
        
        buttons_layout.addWidget(generate_container)
        buttons_layout.addWidget(support_container)
        
        layout.addLayout(buttons_layout)

    def choose_path(self):
        """Выбор пути сохранения"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения рефератов",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if path:
            self.path_input.setText(path)

    def connectSignals(self):
        """Подключение сигналов контроллера"""
        self.controller.progress.connect(self.update_progress)
        self.controller.status.connect(self.update_status)
        self.controller.finished.connect(self.generation_finished)
        self.controller.essay_completed.connect(self.update_completed_essays)

    def start_generation(self):
        """Начало генерации рефератов"""
        topics = self.topics_input.toPlainText().strip().split('\n')
        if not topics or not topics[0]:
            QMessageBox.warning(self, "Ошибка", "Введите хотя бы одну тему!")
            return

        if not self.path_input.text():
            QMessageBox.warning(self, "Ошибка", "Выберите путь для сохранения рефератов!")
            return

        self.completed_essays = []  # Очищаем список готовых рефератов
        self.completed_label.setText("")
        self.generate_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        
        self.controller.generate_essays(
            topics=topics,
            num_chapters=self.chapters_spin.value(),
            symbols_per_chapter=self.symbols_spin.value(),
            output_path=self.path_input.text(),
            language=self.language_combo.currentText()
        )

    def update_progress(self, value: int):
        """Обновление прогресс-бара"""
        self.progress_bar.setValue(value)
        if value > 0:
            remaining = 100 - value
            eta = (remaining * 30) // 100  # Примерно 30 секунд на полную генерацию
            self.status_label.setText(f"Прогресс: {value}% (осталось примерно {eta} сек.)")

    def update_status(self, message: str):
        """Обновление статуса"""
        self.status_label.setText(message)
        self.status_label.repaint()  # Принудительное обновление виджета

    def cancel_generation(self):
        """Отменяет текущую генерацию"""
        if self.controller.worker:
            self.controller.worker.stop_generation = True
            self.status_label.setText("Отмена генерации...")

    def update_completed_essays(self, topic: str):
        """Обновляет список готовых рефератов"""
        self.completed_essays.append(topic)
        if len(self.completed_essays) > 0:
            self.completed_label.setText(
                f"Готовые рефераты: {', '.join(self.completed_essays)}"
            )

    def generation_finished(self, success: bool, message: str):
        """Обработка завершения генерации"""
        self.generate_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        if success:
            QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации: {message}")

    def show_donate_info(self):
        """Показ информации о поддержке проекта"""
        donate_dialog = QDialog(self)
        donate_dialog.setWindowTitle("Поддержать проект")
        donate_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(donate_dialog)
        
        # Текст
        info_text = QLabel(
            "Спасибо, что хотите поддержать проект! 💝\n\n"
            "Все собранные средства идут на оплату API для генерации рефератов "
            "и поддержку разработки. Это позволяет:\n"
            "• Поддерживать проект бесплатным для всех студентов\n"
            "• Улучшать качество генерации\n"
            "• Добавлять новые функции\n"
            "• Увеличивать лимиты на генерацию\n\n"
            "Даже небольшая поддержка очень важна для нас! ❤️"
        )
        info_text.setWordWrap(True)
        layout.addWidget(info_text)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        donate_button = QPushButton("Поддержать")
        donate_button.setStyleSheet(
            "QPushButton {"
            "   background-color: #FF813F;"
            "   color: white;"
            "   padding: 8px 16px;"
            "   border-radius: 4px;"
            "   font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "   background-color: #FF9B66;"
            "}"
        )
        donate_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://buymeacoffee.com/iyulahovicf"))  # Замените на вашу ссылку
        )
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(donate_dialog.close)
        
        buttons_layout.addWidget(donate_button)
        buttons_layout.addWidget(close_button)
        layout.addLayout(buttons_layout)
        
        donate_dialog.exec_()

    def open_telegram(self):
        """Открывает Telegram бота поддержки"""
        QDesktopServices.openUrl(QUrl("https://t.me/v4n4ik"))

    def resizeEvent(self, event):
        """Обработка изменения размера окна"""
        super().resizeEvent(event)
        # Обновляем ширину кнопок при изменении размера окна
        if hasattr(self, 'generate_button'):
            total_width = self.width()
            button_spacing = 20
            margins = 40
            available_width = total_width - margins - (2 * button_spacing)
            
            generate_width = int(available_width * 0.5)
            support_width = int(available_width * 0.25)
            
            self.generate_button.parent().setFixedWidth(generate_width)
            self.donate_button.setFixedWidth(support_width)
            self.telegram_button.setFixedWidth(support_width) 