# -*- coding: utf-8 -*-

import http.client
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class AListAPI:
    """AList API 客户端
    
    处理与 AList 服务器的所有通信，包括：
    - 登录认证
    - 文件列表获取
    - 文件复制
    - 任务状态监控
    """
    
    def __init__(self, host: str, port: int = 5244, use_https: bool = False):
        self.host = f"{host}:{port}"
        self.use_https = use_https
        self.token = None
        self.last_check_time = datetime.now()
        self.active_tasks = set()  # 当前活动的任务ID集合
    
    def _get_connection(self) -> http.client.HTTPConnection:
        """获取 HTTP 连接"""
        if self.use_https:
            return http.client.HTTPSConnection(self.host)
        return http.client.HTTPConnection(self.host)

    def get_file_list(self, path: str) -> Optional[Dict]:
        """获取指定路径的文件列表
        
        Args:
            path: 文件夹路径
            
        Returns:
            Dict: 文件列表数据，失败返回 None
        """
        if not self.token:
            logger.error("未登录")
            return None
            
        conn = self._get_connection()
        headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json'
        }
        
        payload = json.dumps({
            "path": path,
            "password": "",
            "page": 1,
            "per_page": 0,
            "refresh": False
        })
        
        try:
            conn.request("POST", "/api/fs/list", payload, headers)
            response = conn.getresponse()
            data = json.loads(response.read().decode("utf-8"))
            
            if data.get("code") == 200:
                return data
            logger.error(f"获取文件列表失败: {data.get('message')}")
            return None
        except Exception as e:
            logger.error(f"获取文件列表请求失败: {e}")
            return None
        finally:
            conn.close()

    def copy_files(self, src_files: List[str], src_dir: str, dst_dir: str, 
                   max_tasks: int = 3) -> List[str]:
        """批量复制文件"""
        task_ids = []
        
        # 获取当前未完成任务
        undone_result = self.get_undone_tasks()
        if undone_result and undone_result.get("code") == 200:
            undone_tasks = undone_result.get("data", [])
            current_task_count = len(undone_tasks)
            
            # 计算可以创建的新任务数量
            available_slots = max_tasks - current_task_count
            
            if available_slots > 0:
                logger.info(f"当前有 {current_task_count} 个未完成任务，可以创建 {available_slots} 个新任务")
                
                # 只创建允许数量的新任务
                for file_name in src_files[:available_slots]:
                    result = self.copy_file(f"{src_dir}/{file_name}", dst_dir)
                    if result and result.get("code") == 200:
                        tasks = result.get("data", {}).get("tasks", [])
                        if tasks:
                            task_id = tasks[0].get("id")
                            task_ids.append(task_id)
                            # 不再将任务添加到 active_tasks，因为我们现在关注所有任务
                            logger.info(f"创建复制任务: {file_name} -> {task_id}")
                        else:
                            logger.error(f"复制任务创建失败: {file_name}")
                            break
                    else:
                        logger.error(f"复制请求失败: {file_name}")
                        break
            else:
                logger.info(f"当前已有 {current_task_count} 个未完成任务，等待任务完成后再创建新任务")
                return []  # 返回空列表而不是 None
        else:
            logger.error("获取未完成任务列表失败")
        
        return task_ids

    def check_tasks(self, check_interval: int = 60, max_check_time: int = 3600) -> bool:
        """检查任务状态"""
        current_time = datetime.now()
        # 更新最后检查时间
        self.last_check_time = current_time
        
        # 获取未完成任务
        undone_result = self.get_undone_tasks()
        if undone_result and undone_result.get("code") == 200:
            undone_tasks = undone_result.get("data", [])
            
            # 更新所有未完成任务的状态
            for task in undone_tasks:
                task_id = task.get("id")
                status = task.get("status", "")
                progress = task.get("progress", 0)
                error = task.get("error")
                
                if error:
                    logger.error(f"任务出错 {task_id}: {error}")
                else:
                    logger.info(f"任务进度 {task_id}: {progress}% | {status}")
            
            # 返回是否可以创建新任务
            return len(undone_tasks) < 3  # 只要未完成任务总数小于3就可以创建新任务
        
        return False

    def login(self, username: str, password: str) -> bool:
        """登录获取 token"""
        conn = http.client.HTTPConnection(self.host)
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = json.dumps({
            "username": username,
            "password": password
        })
        
        try:
            logger.info(f"尝试登录 {self.host}")
            conn.request("POST", "/api/auth/login", payload, headers)
            response = conn.getresponse()
            login_result = json.loads(response.read().decode("utf-8"))
            
            if login_result.get("code") == 200:
                self.token = login_result.get("data", {}).get("token")
                if self.token:
                    logger.info("登录成功")
                    return True
            logger.error(f"登录失败: {login_result.get('message', '未知错误')}")
            return False
        except Exception as e:
            logger.error(f"登录请求出错: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_undone_tasks(self) -> dict:
        """获取未完成任务列表"""
        if not self.token:
            logger.error("未登录")
            return {}
            
        conn = http.client.HTTPConnection(self.host)
        headers = {
            'Authorization': self.token
        }
        
        try:
            conn.request("GET", "/api/admin/task/copy/undone", "", headers)
            response = conn.getresponse()
            data = json.loads(response.read().decode("utf-8"))
            return data
        except Exception as e:
            logger.error(f"获取未完成任务失败: {str(e)}")
            return {}
        finally:
            conn.close()
    
    def copy_file(self, src_path: str, dst_path: str) -> Optional[Dict]:
        """复制文件"""
        if not self.token:
            logger.error("未登录")
            return None
            
        conn = http.client.HTTPConnection(self.host)
        headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json'
        }
        
        folder_name = src_path.split('/')[-1]
        src_dir = src_path.rsplit('/', 1)[0]
        
        payload = json.dumps({
            "src_dir": src_dir,
            "dst_dir": dst_path,
            "names": [folder_name]
        })
        
        try:
            conn.request("POST", "/api/fs/copy", payload, headers)
            response = conn.getresponse()
            result = json.loads(response.read().decode("utf-8"))
            return result
        except Exception as e:
            logger.error(f"复制文件失败: {str(e)}")
            return None
        finally:
            conn.close()

    def rename_file(self, src_dir: str, src_name: str, new_name: str) -> bool:
        """重命名文件
        
        Args:
            src_dir: 源目录
            src_name: 原文件名
            new_name: 新文件名
            
        Returns:
            bool: 重命名是否成功
        """
        if not self.token:
            logger.error("未登录")
            return False
        
        conn = self._get_connection()
        headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json'
        }
        
        # 构造请求参数
        payload = json.dumps({
            "path": f"{src_dir}/{src_name}",
            "name": new_name
        })
        
        try:
            conn.request("POST", "/api/fs/rename", payload, headers)
            response = conn.getresponse()
            result = json.loads(response.read().decode("utf-8"))
            
            if result.get("code") == 200:
                logger.info(f"重命名成功: {src_name} -> {new_name}")
                return True
            
            logger.error(f"重命名失败: {result.get('message')} | 状态码: {result.get('code')}")
            logger.debug(f"请求参数: {payload}")
            return False
        except Exception as e:
            logger.error(f"重命名请求失败: {e}")
            return False
        finally:
            conn.close()