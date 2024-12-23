import json
import os
import time
import logging
import threading
import schedule
from src.api.alist_api import AListAPI
from src.utils.logger import setup_logger
from src.utils.file_cache import FileCache
from datetime import datetime
from src.web.app import create_app
from logging.handlers import RotatingFileHandler
from typing import List

logger = logging.getLogger(__name__)

class AListCopyService:
    """AList 复制服务
    
    管理文件复制任务的主服务类
    """
    
    def __init__(self, config_file: str = "config/config.json"):
        """初始化服务
        
        Args:
            config_file: 配置文件路径
        """
        self.config = self.load_config(config_file)
        self.logger = setup_logger(os.path.dirname(self.config['log']['file']))
        self.alist = None
        self.cache = None
        self.web_thread = None
        
        # 添加状态相关属性
        self.pending_files = []
        self.active_task_count = 0
        self.total_copied = 0
        self.total_errors = 0
        self.start_time = datetime.now()
        self.last_success_time = None
        
    @staticmethod
    def load_config(config_file: str) -> dict:
        """加载配置文件"""
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def initialize(self) -> bool:
        """初始化服务组件"""
        try:
            # 确保目录存在
            os.makedirs('cache/file_lists', exist_ok=True)
            os.makedirs(os.path.dirname(self.config['log']['file']), exist_ok=True)
            
            # 初始化 API 客户端
            self.alist = AListAPI(
                host=self.config['alist']['host'],
                port=self.config['alist']['port'],
                use_https=self.config['alist']['use_https']
            )
            
            # 登录
            if not self.alist.login(
                self.config['alist']['username'],
                self.config['alist']['password']
            ):
                logger.error("登录失败")
                return False
                
            # 初始化缓存
            self.cache = FileCache(
                'cache/file_lists',
                self.alist,
                self.config
            )
            
            logger.info("服务初始化成功")
            return True
            
        except Exception as e:
            logger.exception("服务初始化失败")
            return False
            
    def start_web_server(self):
        """启动 Web 服务器"""
        def refresh_callback():
            return self.refresh_file_lists()
            
        self.web_thread = threading.Thread(
            target=self._run_web_server,
            args=(refresh_callback,)
        )
        self.web_thread.daemon = True
        self.web_thread.start()
        logger.info(f"Web 监控服务已启动: http://localhost:{self.config['web']['port']}")
        
    def _run_web_server(self, refresh_callback):
        """Web 服务器运行函数"""
        app = create_app(
            os.path.dirname(self.config['log']['file']),
            'cache/file_lists',
            refresh_callback
        )
        app.run(
            host=self.config['web']['host'],
            port=self.config['web']['port'],
            debug=False
        )
        
    def refresh_file_lists(self) -> bool:
        """刷新文件列表缓存"""
        try:
            logger.info("开始刷新文件列表...")
            
            # 获取源文件夹列表
            src_files = self.alist.get_file_list(self.config['sync']['source'])
            if not src_files:
                logger.error("获取源文件列表失败")
                return False
                
            # 获取目标文件夹列表
            dst_files = self.alist.get_file_list(self.config['sync']['target'])
            if not dst_files:
                logger.error("获取目标文件列表失败")
                return False
                
            # 保存缓存
            self.cache.save_file_list(src_files, is_source=True)
            self.cache.save_file_list(dst_files, is_source=False)
            self.cache.update_refresh_time()
            
            # 获取新文件
            new_files = self.cache.get_new_files()
            if new_files:
                logger.info(f"发现 {len(new_files)} 个新文件需要复制")
                return True
                
            logger.info("没有新文件需要复制")
            return False
            
        except Exception as e:
            logger.exception("刷新文件列表失败")
            return False
            
    def check_and_rename_files(self, pending_files: List[str]) -> List[str]:
        """检查并重命名包含特殊字符的文件
        
        Args:
            pending_files: 待处理的文件列表
            
        Returns:
            List[str]: 处理后的文件列表
        """
        renamed_files = []
        src_dir = self.config['sync']['source']
        rename_count = 0
        total_files = len(pending_files)
        
        logger.info(f"开始检查 {total_files} 个文件的命名...")
        
        for file_name in pending_files:
            if "'" in file_name:  # 检查是否包含单引号
                # 生成新文件名
                new_name = file_name.replace("'", "")
                logger.info(f"准备重命名: {file_name} -> {new_name}")
                
                try:
                    # 执行重命名
                    result = self.alist.rename_file(src_dir, file_name, new_name)
                    if result:
                        renamed_files.append(new_name)
                        rename_count += 1
                        logger.info(f"重命名成功 ({rename_count}/{total_files})")
                        
                        # 更新状态
                        self.update_status(
                            current_task=f"重命名文件: {file_name}",
                            progress=int((rename_count / total_files) * 100),
                            total=total_files,
                            completed=rename_count
                        )
                        
                        # 等待文件系统更新
                        time.sleep(10)
                    else:
                        logger.error(f"重命名失败，保留原文件名: {file_name}")
                        renamed_files.append(file_name)
                        self.total_errors += 1
                except Exception as e:
                    logger.error(f"重命名过程出错: {e}")
                    renamed_files.append(file_name)
                    self.total_errors += 1
            else:
                renamed_files.append(file_name)
        
        if rename_count > 0:
            logger.info(f"重命名完成，共处理 {rename_count} 个文件")
            # 刷新源文件列表缓存
            src_files = self.alist.get_file_list(self.config['sync']['source'])
            if src_files:
                self.cache.save_file_list(src_files, is_source=True)
                logger.info("已更新源文件列表缓存")
        else:
            logger.info("没有需要重命名的文件")
        
        return renamed_files

    def run(self):
        """运行服务"""
        try:
            # 设置定时刷新
            schedule.every().day.at("00:00").do(self.refresh_and_start_tasks)
            
            # 初始启动任务
            self.refresh_and_start_tasks()
            
            # 主循环只处理定时任务
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # 每分钟检查一次定时任务
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"定时任务执行出错: {e}")
                    time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("收到停止信号")
            self.shutdown()
        except Exception as e:
            logger.exception("服务运行出错")
            self.shutdown()
        finally:
            logger.info("服务已退出")

    def refresh_and_start_tasks(self):
        """刷新文件列表并启动任务处理"""
        try:
            # 刷新文件列表
            has_new_files = self.refresh_file_lists()
            if not has_new_files:
                logger.info("没有新文件需要处理")
                return
            
            # 获取待复制文件列表
            pending_files = self.cache.get_new_files()
            total_files = len(pending_files)
            logger.info(f"初始化待复制文件列表，共 {total_files} 个文件")
            
            # 检查并重命名文件
            pending_files = self.check_and_rename_files(pending_files)
            
            # 更新初始状态
            self.update_status(
                current_task="等待开始复制任务",
                progress=0,
                total=len(pending_files),
                completed=0
            )
            
            # 启动任务处理线程
            task_thread = threading.Thread(
                target=self._process_tasks,
                args=(pending_files, total_files)
            )
            task_thread.daemon = True
            task_thread.start()
            
        except Exception as e:
            logger.error(f"刷新任务出错: {e}")

    def _process_tasks(self, pending_files: List[str], total_files: int):
        """处理复制任务的线程函数"""
        try:
            no_task_count = 0  # 连续无任务计数
            
            while pending_files:
                try:
                    # 检查任务状态
                    undone_tasks = self.alist.check_tasks(
                        self.config['task']['check_interval'],
                        self.config['task']['max_check_time']
                    )
                    
                    # 更新活动任务数
                    if isinstance(undone_tasks, dict) and 'data' in undone_tasks:
                        tasks = undone_tasks.get('data', [])
                        if isinstance(tasks, list):
                            self.active_task_count = len(tasks)
                            # 记录任务进度
                            for task in tasks:
                                task_id = task.get('id', '')
                                progress = task.get('progress', 0)
                                status = task.get('status', '')
                                logger.info(f"任务进度 {task_id}: {progress}% | {status}")
                            
                            if not tasks:  # 没有活动任务
                                no_task_count += 1
                                if no_task_count >= 5:  # 连续5次没有任务
                                    logger.info("连续5分钟没有检测到任务，停止任务处理")
                                    break
                            else:
                                no_task_count = 0  # 重置计数
                    else:
                        logger.warning("获取任务状态失败")
                        self.active_task_count = 0
                    
                    # 如果有待复制文件，尝试创建新任务
                    if self.active_task_count < self.config['task']['max_concurrent_tasks']:
                        # 创建复制任务
                        task_ids = self.alist.copy_files(
                            pending_files[:3],  # 每次最多处理3个
                            self.config['sync']['source'],
                            self.config['sync']['target'],
                            self.config['task']['max_concurrent_tasks']
                        )
                        
                        if task_ids:  # 有新任务创建成功
                            # 更新夸克网盘缓存
                            dst_files = self.alist.get_file_list(self.config['sync']['target'])
                            if dst_files:
                                self.cache.save_file_list(dst_files, is_source=False)
                                logger.info("已更新夸克网盘缓存")
                            
                            completed_count = len(task_ids)
                            logger.info(f"创建了 {completed_count} 个复制任务")
                            
                            # 从待复制列表中移除已创建任务的文件
                            pending_files = pending_files[completed_count:]
                            self.pending_files = pending_files
                            
                            # 更新状态
                            self.update_status(
                                current_task=pending_files[0] if pending_files else "处理中",
                                progress=int(((total_files - len(pending_files)) / total_files) * 100),
                                total=total_files,
                                completed=completed_count
                            )
                    
                    # 等待下一次检查
                    time.sleep(self.config['task']['check_interval'])
                    
                except Exception as e:
                    logger.error(f"任务处理出错: {e}")
                    time.sleep(5)
            
            logger.info("任务处理完成或已停止")
            
        except Exception as e:
            logger.error(f"任务处理线程出错: {e}")

    def update_status(self, current_task: str, progress: int, total: int, completed: int):
        """更新任务状态"""
        try:
            # 更新统计信息
            if completed > 0:
                self.total_copied += completed
                self.last_success_time = datetime.now()
            
            status = {
                "current_task": current_task,
                "progress": progress,
                "total_tasks": total,
                "completed_tasks": completed,
                "update_time": datetime.now().isoformat(),
                "status_details": {
                    "pending_files": len(self.pending_files),
                    "active_tasks": self.active_task_count,  # 使用类属性
                    "total_copied": self.total_copied,
                    "total_errors": self.total_errors,
                    "last_success": self.last_success_time.isoformat() if self.last_success_time else None
                },
                "statistics": {
                    "start_time": self.start_time.isoformat(),
                    "running_time": str(datetime.now() - self.start_time)
                }
            }
            
            status_file = os.path.join('cache/file_lists', "task_status.json")
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"更新状态失败: {e}")

    def shutdown(self):
        """关闭服务"""
        try:
            logger.info("正在关闭服务...")
            # 保存当前状态
            self.update_status("服务已停止", 0, 0, 0)
            # 等待 web 线程结束
            if self.web_thread and self.web_thread.is_alive():
                self.web_thread.join(timeout=5)
            logger.info("服务已关闭")
        except Exception as e:
            logger.error(f"关闭服务出错: {e}")

def main():
    service = AListCopyService()
    if service.initialize():
        service.start_web_server()
        service.run()

if __name__ == "__main__":
    main() 