from typing import Tuple
from LFU import LFUCache
from hard_drive import HDD
from access_planners import FIFOScheduler, LOOKScheduler, NLOOKScheduler
import numpy as np


class HDDController:
    def __init__(self,
                 rpm: int = 7500,
                 sectors_num: int = 500,
                 tracks_num: int = 10000,
                 cache_left: int = 5,
                 cache_middle: int = 10,
                 cache_total: int = 20,
                 scheduler_type: str = 'LOOK',
                 syscall_read_delay: float = 0.15,
                 syscall_write_delay: float = 0.15,
                 interrupt_handling_delay: float = 0.05,
                 user_process_read_delay: float = 7.0,
                 user_process_write_delay: float = 7.0,
                 cache_access_delay: float = 0.01):
        """
        Ініціалізує контролер жорсткого диска з усіма затримками

        Args:
            rpm: Швидкість обертання диска (об/хв)
            sectors_num: Кількість секторів на доріжці
            tracks_num: Кількість доріжок
            cache_left: Розмір лівого сегмента кешу
            cache_middle: Розмір середнього сегмента кешу
            cache_total: Загальний розмір кешу
            scheduler_type: Тип планувальника ('FIFO' або 'LOOK')
            syscall_read_delay: Затримка системного виклику читання (мс)
            syscall_write_delay: Затримка системного виклику запису (мс)
            interrupt_handling_delay: Затримка обробки переривання (мс)
            user_process_read_delay: Затримка обробки даних після читання (мс)
            user_process_write_delay: Затримка формування даних для запису (мс)
            cache_access_delay: Затримка доступу до кешу (мс)
        """
        # Ініціалізація компонентів
        self.hdd = HDD(rpm=rpm, sectors_num=sectors_num, track_num=tracks_num)
        self.cache = LFUCache(max_left=cache_left,
                              max_middle=cache_middle,
                              max_total=cache_total)

        # Вибір планувальника
        if scheduler_type.upper() == 'FIFO':
            self.scheduler = FIFOScheduler(self.hdd)
        elif scheduler_type.upper() == 'LOOK':
            self.scheduler = LOOKScheduler(self.hdd)
        else:
            self.scheduler = NLOOKScheduler(self.hdd)

        # Затримки
        self.syscall_read_delay = syscall_read_delay
        self.syscall_write_delay = syscall_write_delay
        self.interrupt_handling_delay = interrupt_handling_delay
        self.user_process_read_delay = user_process_read_delay
        self.user_process_write_delay = user_process_write_delay
        self.cache_access_delay = cache_access_delay

        # Статистика роботи
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_delay = 0

    def read_sector(self, sector_num: int) -> Tuple[np.ndarray, float, bool]:
        """
        Читає дані з вказаного сектора

        Args:
            sector_num: Абсолютний номер сектора

        Returns:
            Tuple[np.ndarray, float, bool]: (дані сектора, загальна затримка, чи був це кеш-хіт)
        """
        total_delay = self.syscall_read_delay

        # Спроба читання з кешу
        cached_data = self.cache.get_sector(sector_num)

        if cached_data is not None:
            self.cache_hits += 1
            total_delay += self.cache_access_delay
            total_delay += self.user_process_read_delay
            self.total_delay += total_delay
            return cached_data, total_delay, True

        self.cache_misses += 1

        # Читання з диска через планувальник
        result = self.scheduler.add_request(sector_num, is_write=False)

        if result is None:
            raise ValueError(f"Помилка читання сектора {sector_num}")

        data, disk_delay = result
        total_delay += disk_delay
        total_delay += self.interrupt_handling_delay
        total_delay += self.user_process_read_delay

        self.total_delay += total_delay

        # Додавання прочитаних даних в кеш
        self.cache.add_sector(sector_num, data)

        return data, total_delay, False

    def write_sector(self, sector_num: int, data: np.ndarray) -> Tuple[float, dict]:
        """
        Записує дані у вказаний сектор

        Args:
            sector_num: Абсолютний номер сектора
            data: Дані для запису

        Returns:
            Tuple[float, dict]: (загальна затримка, словник з деталями затримок)
        """
        delays = {
            'syscall': self.syscall_write_delay,
            'user_process': self.user_process_write_delay,
            'disk_operation': 0,
            'interrupt': self.interrupt_handling_delay
        }

        total_delay = delays['syscall'] + delays['user_process']

        # Запис через планувальник
        disk_delay = self.scheduler.add_request(sector_num, is_write=True, data=data)

        if disk_delay is None:
            raise ValueError(f"Помилка запису в сектор {sector_num}")

        delays['disk_operation'] = disk_delay
        total_delay += disk_delay + delays['interrupt']

        self.total_delay += total_delay

        # Оновлення даних в кеші
        self.cache.add_sector(sector_num, data)

        return total_delay, delays

    def get_statistics(self) -> dict:
        """Повертає статистику роботи контролера"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': hit_rate,
            'total_delay': self.total_delay,
            'delays': {
                'syscall_read': self.syscall_read_delay,
                'syscall_write': self.syscall_write_delay,
                'interrupt': self.interrupt_handling_delay,
                'user_read': self.user_process_read_delay,
                'user_write': self.user_process_write_delay,
                'cache_access': self.cache_access_delay
            }
        }