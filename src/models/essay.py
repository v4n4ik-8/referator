from dataclasses import dataclass
from typing import List

@dataclass
class Section:
    title: str
    content: str
    is_chapter: bool = False

@dataclass
class Essay:
    topic: str
    sections: List[Section]
    num_chapters: int
    symbols_per_chapter: int
    
    @property
    def filename(self) -> str:
        """Генерирует имя файла для реферата"""
        return f"реферат_{self.topic.replace(':', '_').replace(' ', '_')}.docx"
    
    def validate(self) -> bool:
        """Проверяет корректность структуры реферата"""
        if not self.sections:
            return False
            
        # Проверяем наличие введения
        if "Введение" not in self.sections[0].title:
            return False
            
        # Проверяем количество глав
        chapters = [s for s in self.sections if s.is_chapter]
        if len(chapters) != self.num_chapters:
            return False
            
        return True 