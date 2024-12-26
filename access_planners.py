from collections import deque
from dataclasses import dataclass
from enum import Enum
import numpy as np


@dataclass
class DiskRequest:
    sector: int
    is_write: bool
    data: np.ndarray = None


class Direction(Enum):
    UP = 1
    DOWN = 2


class FIFOScheduler:
    def __init__(self, hdd):
        self.hdd = hdd
        self.queue = deque()

    def add_request(self, sector, is_write=False, data=None):
        request = DiskRequest(sector=sector, is_write=is_write, data=data)

        # Додаємо запит до черги і одразу обробляємо його
        self.queue.append(request)
        return self._process_request(request)

    def _process_request(self, request):
        try:
            if request.is_write and request.data is not None:
                delay = self.hdd.write_sector(request.sector, request.data)
                return delay
            else:
                data, delay = self.hdd.read_sector(request.sector)
                return (data, delay)
        except Exception as e:
            print(f"Помилка при обробці запиту: {e}")
            return None


class LOOKScheduler:
    def __init__(self, hdd, max_same_track_requests=3):
        self.hdd = hdd
        self.max_same_track_requests = max_same_track_requests
        self.queue = []
        self.direction = Direction.UP

    def add_request(self, sector, is_write=False, data=None):
        request = DiskRequest(sector=sector, is_write=is_write, data=data)

        # Додаємо запит та сортуємо чергу
        self.queue.append(request)
        self.queue.sort(key=lambda x: x.sector)

        # Знаходимо та обробляємо наступний запит
        next_request = self._find_next_request()
        if next_request:
            self.queue.remove(next_request)
            return self._process_request(next_request)
        return None

    def _find_next_request(self):
        if not self.queue:
            return None

        current_track = self.hdd.rw_head_position
        same_track_count = 0

        if self.direction == Direction.UP:
            for request in self.queue:
                request_track = request.sector // self.hdd.sectors_per_track
                if request_track >= current_track:
                    if request_track == current_track:
                        same_track_count += 1
                        if same_track_count > self.max_same_track_requests:
                            continue
                    return request

            self.direction = Direction.DOWN
            return self._find_next_request()

        else:
            for request in reversed(self.queue):
                request_track = request.sector // self.hdd.sectors_per_track
                if request_track <= current_track:
                    if request_track == current_track:
                        same_track_count += 1
                        if same_track_count > self.max_same_track_requests:
                            continue
                    return request

            self.direction = Direction.UP
            return self._find_next_request()

    def _process_request(self, request):
        try:
            if request.is_write and request.data is not None:
                delay = self.hdd.write_sector(request.sector, request.data)
                return delay
            else:
                data, delay = self.hdd.read_sector(request.sector)
                return (data, delay)
        except Exception as e:
            print(f"Помилка при обробці запиту: {e}")
            return None


class NLOOKScheduler:
    def __init__(self, hdd, max_track_span=100):
        self.hdd = hdd
        self.max_track_span = max_track_span
        self.queue = []
        self.direction = Direction.UP

    def add_request(self, sector, is_write=False, data=None):
        request = DiskRequest(sector=sector, is_write=is_write, data=data)
        self.queue.append(request)
        self.queue.sort(key=lambda x: x.sector)

        next_request = self._find_next_request()
        if next_request:
            self.queue.remove(next_request)
            return self._process_request(next_request)
        return None

    def _find_next_request(self):
        if not self.queue:
            return None

        current_track = self.hdd.rw_head_position // self.hdd.sectors_per_track
        if self.direction == Direction.UP:
            for request in self.queue:
                request_track = request.sector // self.hdd.sectors_per_track
                if request_track >= current_track and request_track <= current_track + self.max_track_span:
                    return request
            self.direction = Direction.DOWN
        elif self.direction == Direction.DOWN:
            for request in reversed(self.queue):
                request_track = request.sector // self.hdd.sectors_per_track
                if request_track <= current_track and request_track >= current_track - self.max_track_span:
                    return request
            self.direction = Direction.UP
        return None

    def _process_request(self, request):
        try:
            if request.is_write and request.data is not None:
                delay = self.hdd.write_sector(request.sector, request.data)
                return delay
            else:
                data, delay = self.hdd.read_sector(request.sector)
                return (data, delay)
        except Exception as e:
            print(f"Помилка при обробці запиту: {e}")
            return None

