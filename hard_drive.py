import numpy as np

class HDD:
    def __init__(self, rpm=7500, sectors_num=500, track_num=10000):
        self.rpm = rpm
        self.track_number = track_num   # Кількість доріжок
        self.sectors_per_track = sectors_num    # Кількість секторів на доріжці
        self.sector_size = 512      # Розмір одного сектора
        self.rw_head_position = 0
        self.data = np.zeros(sectors_num * track_num)
        self.rotation_delay = ((60*1000)/self.rpm)/2
        self.rw_delay = ((60*1000)/self.rpm)/self.sectors_per_track
        self.max_reach_delay = 10   # Максимальна затримка переведення головки
        self.one_step_delay = 0.5   # Затримка переведення головки на одну доріжку

    def read_sector(self, abs_sector_num):
        """
        Читає дані з вказаного сектора

        Args:
            abs_sector_num (int): Абсолютний номер сектора

        Returns:
            tuple: (дані сектора, затримка операції)
        """
        if not (0 <= abs_sector_num < self.track_number * self.sectors_per_track):
            raise ValueError("Невірний номер сектора")

        # Отримуємо дані
        curr_data = self.data[abs_sector_num:abs_sector_num + self.sector_size]

        # Обчислюємо затримку
        track_num = abs_sector_num // self.sectors_per_track
        track_reach_delay = min(float(self.max_reach_delay), abs(self.rw_head_position - track_num)*self.one_step_delay)
        sector_rw_delay = self.rw_delay + self.rotation_delay
        delay = track_reach_delay + sector_rw_delay

        # Оновлюємо позицію головки
        self.rw_head_position = track_num

        return curr_data.copy(), delay

    def write_sector(self, abs_sector_num, data):
        """
        Записує дані у вказаний сектор

        Args:
            abs_sector_num (int): Абсолютний номер сектора
            data (numpy.array): Дані для запису

        Returns:
            float: Затримка операції
        """
        if not (0 <= abs_sector_num < self.track_number * self.sectors_per_track):
            raise ValueError("Невірний номер сектора")

        if len(data) != self.sector_size:
            raise ValueError(f"Розмір даних повинен бути {self.sector_size} байт")

        # Обчислюємо затримку так само, як і при читанні
        track_num = abs_sector_num // self.sectors_per_track
        track_delta = abs(self.rw_head_position - track_num)
        track_reach_delay = min(float(self.max_reach_delay), track_delta*self.one_step_delay)
        sector_rw_delay = self.rw_delay + self.rotation_delay
        total_delay = track_reach_delay + sector_rw_delay

        # Записуємо дані
        self.data[abs_sector_num:abs_sector_num + self.sector_size] = data

        # Оновлюємо позицію головки
        self.rw_head_position = abs_sector_num // self.sectors_per_track

        return total_delay


