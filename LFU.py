class LFUCache:
    def __init__(self, max_left, max_middle, max_total):
        self.max_left = max_left
        self.max_middle = max_middle
        self.max_total = max_total

        self.left_segment = []
        self.middle_segment = []
        self.right_segment = []
        self.time = 0

        # Словник для швидкого пошуку буферів за номером сектора
        self.sector_map = {}

    def get_sector(self, sector_number):
        """
        Повертає дані сектора якщо він є в кеші,
        інакше повертає None
        """
        self.time += 1

        if sector_number in self.sector_map:
            buffer = self.sector_map[sector_number]
            buffer.access(self.time)
            self._move_to_left(buffer)
            return buffer.data

        return None

    def add_sector(self, sector_number, data):
        """Додає новий сектор в кеш"""
        self.time += 1

        # Якщо сектор вже є в кеші, оновлюємо дані
        if sector_number in self.sector_map:
            buffer = self.sector_map[sector_number]
            buffer.data = data
            buffer.access(self.time)
            self._move_to_left(buffer)
            return

        # Створюємо новий буфер
        new_buffer = Buffer(sector_number, data)
        new_buffer.access(self.time)
        self._add_to_left(new_buffer)

    def _move_to_left(self, buffer):
        """Переміщує буфер у лівий сегмент"""
        # Видаляємо буфер з поточного сегмента
        for segment in [self.middle_segment, self.right_segment]:
            if buffer in segment:
                segment.remove(buffer)
                break

        self._add_to_left(buffer)

    def _add_to_left(self, buffer):
        """Додає буфер у лівий сегмент"""
        if len(self.left_segment) >= self.max_left:
            moved_buffer = self.left_segment.pop(-1)
            self._add_to_middle(moved_buffer)

        self.left_segment.insert(0, buffer)
        self.sector_map[buffer.sector_number] = buffer

    def _add_to_middle(self, buffer):
        """Додає буфер у середній сегмент"""
        if len(self.middle_segment) >= self.max_middle:
            moved_buffer = self.middle_segment.pop(-1)
            self._add_to_right(moved_buffer)

        self.middle_segment.insert(0, buffer)

    def _add_to_right(self, buffer):
        """Додає буфер у правий сегмент"""
        # Якщо правий сегмент повний, видаляємо буфер з найменшим лічильником
        if len(self.right_segment) >= (self.max_total - self.max_left - self.max_middle):
            # Шукаємо буфер з найменшим лічильником з кінця списку
            min_counter = float('inf')
            min_index = -1

            for i in range(len(self.right_segment) - 1, -1, -1):
                if self.right_segment[i].counter < min_counter:
                    min_counter = self.right_segment[i].counter
                    min_index = i

            # Видаляємо знайдений буфер
            removed_buffer = self.right_segment.pop(min_index)
            del self.sector_map[removed_buffer.sector_number]

        self.right_segment.insert(0, buffer)

    def display(self):
        """Виводить стан сегментів"""
        print("Left Segment:", self.left_segment)
        print("Middle Segment:", self.middle_segment)
        print("Right Segment:", self.right_segment)


class Buffer:
    def __init__(self, sector_number, data):
        self.sector_number = sector_number  # Номер сектора
        self.data = data  # Дані сектора
        self.counter = 0  # Лічильник використання
        self.last_access_time = 0  # Час останнього доступу

    def access(self, time):
        """Оновлює статистику доступу до буфера"""
        self.counter += 1
        self.last_access_time = time

    def __repr__(self):
        return f"Buffer(sector={self.sector_number}, counter={self.counter})"