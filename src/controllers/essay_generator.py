from typing import List
import os
from PySide6.QtCore import QObject, Signal, QThread
from models import Essay, Section, APIClient
from models.api_client import APIError
from utils import DocumentFormatter

class GeneratorWorker(QThread):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(bool, str)
    essay_completed = Signal(str)  # Сигнал о готовом реферате
    
    def __init__(self, topics: List[str], num_chapters: int, symbols_per_chapter: int, output_path: str, language: str = "Русский"):
        super().__init__()
        self.topics = topics
        self.num_chapters = num_chapters
        self.symbols_per_chapter = symbols_per_chapter
        self.output_path = output_path
        self.language = language
        self.api_client = APIClient()
        self.formatter = DocumentFormatter()
        self.stop_generation = False
        
    def run(self):
        try:
            total_steps = len(self.topics) * (self.num_chapters + 1)  # +1 для введения
            current_step = 0
            
            for topic in self.topics:
                if self.stop_generation:
                    self.status.emit("Генерация отменена")
                    self.finished.emit(False, "Генерация была отменена пользователем")
                    return

                self.status.emit(f"Генерация структуры реферата: {topic}")
                
                # Получаем структуру реферата
                structure = self.api_client.get_essay_structure(topic, self.num_chapters, self.language)
                if not structure:
                    raise Exception(f"Не удалось получить структуру для темы: {topic}")
                
                # Разбираем структуру на секции
                section_titles = [line.strip() for line in structure.split('\n') if line.strip()]
                sections = []
                
                # Генерируем содержимое для каждой секции
                for title in section_titles:
                    if self.stop_generation:
                        self.status.emit("Генерация отменена")
                        self.finished.emit(False, "Генерация была отменена пользователем")
                        return

                    self.status.emit(f"Генерация раздела: {title}")
                    
                    content = self.api_client.generate_section_content(
                        topic, 
                        title,
                        self.symbols_per_chapter,
                        self.language
                    )
                    
                    if not content:
                        raise Exception(f"Не удалось сгенерировать содержимое для раздела: {title}")
                    
                    is_chapter = "Глава" in title
                    sections.append(Section(title=title, content=content, is_chapter=is_chapter))
                    
                    current_step += 1
                    progress = (current_step * 100) // total_steps
                    self.progress.emit(progress)
                
                # Создаем объект реферата
                essay = Essay(
                    topic=topic,
                    sections=sections,
                    num_chapters=self.num_chapters,
                    symbols_per_chapter=self.symbols_per_chapter
                )
                
                # Проверяем корректность структуры
                if not essay.validate():
                    raise Exception(f"Некорректная структура реферата для темы: {topic}")
                
                # Создаем и сохраняем документ
                doc = self.formatter.create_document(essay)
                
                # Формируем имя файла и путь
                safe_filename = "".join(x for x in topic if x.isalnum() or x in (' ', '-', '_')).strip()
                safe_filename = f"Реферат - {safe_filename}.docx"
                full_path = os.path.join(self.output_path, safe_filename)
                
                # Сохраняем документ
                doc.save(full_path)
                
                # Сигнализируем о готовом реферате
                self.essay_completed.emit(topic)
            
            self.finished.emit(True, "Рефераты успешно сгенерированы! 🎉")
            
        except APIError as e:
            self.status.emit(e.user_message)
            self.finished.emit(False, e.user_message)
        except Exception as e:
            error_message = (
                "Что-то пошло не так... 😔\n\n"
                "Возможные причины:\n"
                "• Слишком сложная тема\n"
                "• Временные проблемы с сервисом\n"
                "• Проблемы с подключением\n\n"
                "Попробуйте упростить тему или повторить попытку позже."
            )
            self.status.emit(error_message)
            self.finished.emit(False, error_message)

class EssayGeneratorController(QObject):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(bool, str)
    essay_completed = Signal(str)  # Прокидываем сигнал дальше
    
    def __init__(self):
        super().__init__()
        self.worker = None
    
    def generate_essays(self, topics: List[str], num_chapters: int, symbols_per_chapter: int, output_path: str, language: str = "Русский") -> None:
        """Генерирует рефераты для списка тем"""
        # Создаем и настраиваем worker
        self.worker = GeneratorWorker(topics, num_chapters, symbols_per_chapter, output_path, language)
        
        # Подключаем сигналы
        self.worker.progress.connect(self.progress.emit)
        self.worker.status.connect(self.status.emit)
        self.worker.finished.connect(self.finished.emit)
        self.worker.essay_completed.connect(self.essay_completed.emit)
        
        # Запускаем генерацию в отдельном потоке
        self.worker.start() 