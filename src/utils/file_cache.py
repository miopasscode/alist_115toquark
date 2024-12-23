import json
import os
from typing import List, Tuple, Dict
from datetime import datetime
import logging
from src.api.alist_api import AListAPI

logger = logging.getLogger(__name__)

class FileCache:
    """文件缓存管理类
    
    负责管理115网盘和夸克网盘的文件列表缓存，
    包括缓存的读取、更新和对比功能。
    """
    
    def __init__(self, cache_dir: str, alist_client: AListAPI, config: dict):
        """初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径
            alist_client: AList API 客户端
            config: 配置信息
        """
        self.cache_dir = cache_dir
        self.alist = alist_client
        self.config = config
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # 缓存文件路径
        self.src_cache_file = os.path.join(cache_dir, "115_files.json")
        self.dst_cache_file = os.path.join(cache_dir, "quark_files.json")
        self.last_refresh_file = os.path.join(cache_dir, "last_refresh.json")
    
    def need_refresh(self, refresh_interval: int) -> bool:
        """检查是否需要刷新缓存
        
        Args:
            refresh_interval: 刷新间隔（秒）
            
        Returns:
            bool: 是否需要刷新
        """
        try:
            if os.path.exists(self.last_refresh_file):
                with open(self.last_refresh_file, 'r') as f:
                    last_refresh = json.load(f)
                    last_time = datetime.fromisoformat(last_refresh['time'])
                    return (datetime.now() - last_time).total_seconds() > refresh_interval
            return True
        except Exception as e:
            logger.error(f"检查刷新时间失败: {e}")
            return True
    
    def update_refresh_time(self):
        """更新最后刷新时间"""
        with open(self.last_refresh_file, 'w') as f:
            json.dump({'time': datetime.now().isoformat()}, f)
    
    def save_file_list(self, file_list: Dict, is_source: bool = True):
        """保存文件列表到缓存
        
        Args:
            file_list: 文件列表数据
            is_source: 是否是源文件夹（115网盘）
        """
        cache_file = self.src_cache_file if is_source else self.dst_cache_file
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(file_list, f, ensure_ascii=False, indent=2)
    
    def get_new_files(self) -> List[str]:
        """获取需要复制的新文件列表"""
        try:
            # 读取源文件列表 (115网盘)
            with open(self.src_cache_file, 'r', encoding='utf-8') as f:
                src_data = json.load(f)
            
            # 读取目标缓存文件列表 (夸克网盘缓存)
            with open(self.dst_cache_file, 'r', encoding='utf-8') as f:
                dst_cache_data = json.load(f)
            
            # 获取源文件夹名称集合
            src_folders = {
                item["name"] 
                for item in src_data.get("data", {}).get("content", [])
                if item.get("is_dir")
            }
            
            # 获取目标缓存中的文件夹名称集合
            dst_cache_folders = {
                item["name"] 
                for item in dst_cache_data.get("data", {}).get("content", [])
                if item.get("is_dir")
            }
            
            # 获取目标实时文件列表 (夸克网盘实时)
            dst_files = self.alist.get_file_list(self.config['paths']['dst_folder'])
            if dst_files:
                dst_real_folders = {
                    item["name"] 
                    for item in dst_files.get("data", {}).get("content", [])
                    if item.get("is_dir")
                }
            else:
                dst_real_folders = set()
            
            # 合并目标文件夹集合（缓存 + 实时）
            dst_folders = dst_cache_folders | dst_real_folders
            
            # 返回需要复制的文件列表（在源中有但目标中没有的文件）
            new_files = src_folders - dst_folders
            return sorted(list(new_files))
            
        except Exception as e:
            logger.error(f"获取新文件列表失败: {e}")
            return []