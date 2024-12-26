import numpy as np
from controller import HDDController


def test_hdd_controller():
    """
    Розширена функція тестування з симуляцією роботи декількох процесів
    """
    print("\n" + "=" * 50)
    print("МОДЕЛЮВАННЯ РОБОТИ КОНТРОЛЕРА ЖОРСТКОГО ДИСКУ")
    print("=" * 50 + "\n")

    # Створення контролера
    controller = HDDController(
        rpm=300,
        sectors_num=1000,
        tracks_num=50000,
        cache_left=5,
        cache_middle=10,
        cache_total=20,
        scheduler_type='FIFO'
    )

    # Виведення початкових параметрів
    print("ПАРАМЕТРИ ЖОРСТКОГО ДИСКУ:")
    print("-" * 30)
    print(f"Швидкість обертання: {controller.hdd.rpm} об/хв")
    print(f"Кількість секторів на доріжці: {controller.hdd.sectors_per_track}")
    print(f"Кількість доріжок: {controller.hdd.track_number}")
    print(f"Розмір сектора: {controller.hdd.sector_size} байт")
    print(f"Середня затримка обертання: {controller.hdd.rotation_delay:.2f} мс")
    print(f"Затримка читання/запису сектора: {controller.hdd.rw_delay:.2f} мс")
    print(f"Максимальна затримка переміщення головки: {controller.hdd.max_reach_delay} мс")

    print("\nЗАТРИМКИ СИСТЕМИ:")
    print("-" * 30)
    print(f"Системний виклик читання: {controller.syscall_read_delay} мс")
    print(f"Системний виклик запису: {controller.syscall_write_delay} мс")
    print(f"Обробка переривання: {controller.interrupt_handling_delay} мс")
    print(f"Обробка даних після читання: {controller.user_process_read_delay} мс")
    print(f"Формування даних для запису: {controller.user_process_write_delay} мс")
    print(f"Доступ до кешу: {controller.cache_access_delay} мс")

    print("\nПАРАМЕТРИ КЕШУ:")
    print("-" * 30)
    print(f"Розмір лівого сегменту: {controller.cache.max_left}")
    print(f"Розмір середнього сегменту: {controller.cache.max_middle}")
    print(f"Загальний розмір: {controller.cache.max_total}")

    # Симуляція процесів
    processes = {
        'FinAnalytics': {
            'read_sectors': [3000, 3001, 3002, 45000, 45001, 45002],
            'write_sectors': [3000, 45000]
        },
        'DocProcessor': {
            'read_sectors': [1000, 25000, 49999, 35000],
            'write_sectors': [1000, 49999]
        },
        'DataVis': {
            'read_sectors': [15000, 30000, 42000],
            'write_sectors': [15000]
        }
    }

    test_data = np.ones(512)  # Тестові дані для запису

    print("\nМОДЕЛЮВАННЯ РОБОТИ ПРОЦЕСІВ:")
    print("=" * 50)

    # Симуляція операцій для кожного процесу
    for process_name, operations in processes.items():
        print(f"\nПроцес: {process_name}")
        print("-" * 30)

        # Операції запису
        print("\nОперації запису:")
        for sector in operations['write_sectors']:
            try:
                delay, delays = controller.write_sector(sector, test_data)
                print(f"Сектор {sector:6d}: загальна затримка = {delay:8.2f} мс")
                print(f"  - Системний виклик: {delays['syscall']:.2f} мс")
                print(f"  - Формування даних: {delays['user_process']:.2f} мс")
                print(f"  - Операція диску: {delays['disk_operation']:.2f} мс")
                print(f"  - Обробка переривання: {delays['interrupt']:.2f} мс")
            except Exception as e:
                print(f"Помилка запису в сектор {sector}: {e}")

        # Операції читання
        print("\nОперації читання:")
        for sector in operations['read_sectors']:
            try:
                data, delay, is_hit = controller.read_sector(sector)
                status = "HIT" if is_hit else "MISS"
                print(f"Сектор {sector:6d}: затримка = {delay:8.2f} мс [{status}]")
                print(f"  - {'Читання з кешу' if is_hit else 'Читання з диску'}")
                print(f"  - Системний виклик: {controller.syscall_read_delay:.2f} мс")
                if is_hit:
                    print(f"  - Доступ до кешу: {controller.cache_access_delay:.2f} мс")
                else:
                    print(
                        f"  - Операція диску: {delay - controller.syscall_read_delay - controller.interrupt_handling_delay - controller.user_process_read_delay:.2f} мс")
                    print(f"  - Обробка переривання: {controller.interrupt_handling_delay:.2f} мс")
                print(f"  - Обробка даних: {controller.user_process_read_delay:.2f} мс")
            except Exception as e:
                print(f"Помилка читання сектора {sector}: {e}")

    # Виведення підсумкової статистики
    print("\nПІДСУМКОВА СТАТИСТИКА:")
    print("=" * 50)
    stats = controller.get_statistics()

    total_requests = stats['cache_hits'] + stats['cache_misses']
    print(f"\nЗагальна кількість запитів: {total_requests}")
    print(f"Кількість влучань в кеш: {stats['cache_hits']}")
    print(f"Кількість промахів кешу: {stats['cache_misses']}")
    print(f"Відсоток влучань: {stats['hit_rate']:.2f}%")
    print(f"Загальна затримка: {stats['total_delay']:.2f} мс")
    print(f"Середня затримка на запит: {(stats['total_delay'] / total_requests):.2f} мс")


if __name__ == "__main__":
    test_hdd_controller()