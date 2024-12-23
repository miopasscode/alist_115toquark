from datetime import datetime

class TaskStatistics:
    def __init__(self):
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.total_files = 0
        self.total_size = 0
        self.start_time = datetime.now()
        self.history = []

    def add_task(self, task_info: dict):
        self.total_tasks += 1
        self.history.append({
            "time": datetime.now().isoformat(),
            "type": "new",
            "task": task_info
        })

    def update_task(self, task_id: str, status: str, progress: int):
        if status == "succeeded":
            self.completed_tasks += 1
        elif status == "failed":
            self.failed_tasks += 1

    def get_summary(self) -> dict:
        return {
            "total_tasks": self.total_tasks,
            "completed": self.completed_tasks,
            "failed": self.failed_tasks,
            "success_rate": f"{(self.completed_tasks/self.total_tasks)*100:.2f}%",
            "running_time": str(datetime.now() - self.start_time)
        } 