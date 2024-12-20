import threading
import uuid
import queue
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskQueue:
    def __init__(self, num_workers=3):
        self.queue = queue.Queue()
        self.tasks = {}
        self.workers = []
        self.num_workers = num_workers
        self._start_workers()
        
    def _start_workers(self):
        """Запускает рабочие потоки"""
        for _ in range(self.num_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)
            
    def _worker_loop(self):
        """Основной цикл рабочего потока"""
        while True:
            try:
                # Получаем задачу из очереди
                task_id, func, args, kwargs = self.queue.get()
                logger.info(f"Processing task {task_id}")
                
                try:
                    # Добавляем task_id к потоку для отслеживания состояния
                    threading.current_thread().task_id = task_id
                    
                    # Выполняем задачу
                    result = func(*args, **kwargs)
                    logger.info(f"Task {task_id} completed with result: {result}")
                    
                    # Сохраняем результат
                    self.tasks[task_id].update({
                        'state': 'COMPLETED',
                        'result': result
                    })
                    
                except Exception as e:
                    logger.error(f"Task {task_id} failed with error: {str(e)}")
                    self.tasks[task_id].update({
                        'state': 'FAILED',
                        'error': str(e)
                    })
                    
                finally:
                    self.queue.task_done()
                    
            except Exception as e:
                logger.error(f"Worker loop error: {str(e)}")
                
    def add_task(self, func, *args, **kwargs):
        """Добавляет новую задачу в очередь"""
        task_id = str(uuid.uuid4())
        logger.info(f"Adding new task {task_id}")
        
        # Создаем запись о за��аче
        self.tasks[task_id] = {
            'state': 'PENDING',
            'result': None,
            'error': None
        }
        
        # Добавляем задачу в очередь
        self.queue.put((task_id, func, args, kwargs))
        return task_id
        
    def get_task_status(self, task_id):
        """Возвращает статус задачи"""
        if task_id not in self.tasks:
            return {'success': False, 'error': 'Task not found'}
            
        task = self.tasks[task_id]
        
        if task['state'] == 'COMPLETED':
            return task['result']
        elif task['state'] == 'FAILED':
            return {'success': False, 'error': task['error']}
        else:
            return {'success': True, 'state': task['state']}
            
    def update_task_state(self, task_id, state):
        """Обновляет состояние задачи"""
        if task_id in self.tasks:
            logger.info(f"Updating task {task_id} state to {state}")
            self.tasks[task_id]['state'] = state

# Создаем глобальный экземпляр очереди задач
task_queue = TaskQueue()
