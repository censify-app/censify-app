import threading
import queue
import uuid
from typing import Dict, Any
import time
from config import Config

class TaskStatus:
    def __init__(self):
        self.state = 'PENDING'
        self.result = None
        self.error = None

class TaskThread(threading.Thread):
    def __init__(self, task_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_id = task_id

class TaskQueue:
    def __init__(self, num_workers=Config.TASK_QUEUE_WORKERS):
        self.task_queue = queue.Queue()
        self.tasks: Dict[str, TaskStatus] = {}
        self.workers = []
        
        # Запускаем воркеры
        for _ in range(num_workers):
            worker = TaskThread(task_id=None, target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def _worker_loop(self):
        while True:
            try:
                # Получаем задачу из очереди
                task_id, func, args, kwargs = self.task_queue.get()
                
                # Обновляем task_id текущего потока
                threading.current_thread().task_id = task_id
                task_status = self.tasks[task_id]
                
                try:
                    # Выполняем задачу
                    result = func(*args, **kwargs)
                    task_status.result = result
                    task_status.state = 'SUCCESS'
                except Exception as e:
                    task_status.error = str(e)
                    task_status.state = 'ERROR'
                finally:
                    # Очищаем task_id потока
                    threading.current_thread().task_id = None
                
            except Exception as e:
                print(f"Worker error: {e}")
            finally:
                self.task_queue.task_done()
    
    def add_task(self, func, *args, **kwargs) -> str:
        # Создаем ID задачи
        task_id = str(uuid.uuid4())
        
        # Создаем статус задачи
        self.tasks[task_id] = TaskStatus()
        
        # Добавляем задачу в очередь
        self.task_queue.put((task_id, func, args, kwargs))
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        if task_id not in self.tasks:
            return {'success': False, 'error': 'Task not found'}
            
        task_status = self.tasks[task_id]
        
        if task_status.state == 'SUCCESS':
            return task_status.result
        elif task_status.state == 'ERROR':
            return {'success': False, 'error': task_status.error}
        else:
            return {'success': True, 'state': task_status.state}
    
    def update_task_state(self, task_id: str, state: str):
        if task_id in self.tasks:
            self.tasks[task_id].state = state

# Глобальный экземпляр очереди задач
task_queue = TaskQueue()
