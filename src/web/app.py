from flask import Flask, render_template, jsonify, request
import logging
import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class TaskMonitor:
    def __init__(self, log_dir: str, cache_dir: str, refresh_callback=None):
        self.log_dir = log_dir
        self.cache_dir = cache_dir
        self.refresh_callback = refresh_callback
        
    def get_latest_logs(self, lines: int = 100) -> list:
        """获取最新的日志"""
        log_file = os.path.join(
            self.log_dir, 
            "copy_task.log"
        )
        if not os.path.exists(log_file):
            return []
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return list(f.readlines())[-lines:]
        except Exception as e:
            logger.error(f"读取日志失败: {e}")
            return []
    
    def get_task_status(self) -> dict:
        """获取任务状态"""
        try:
            status_file = os.path.join(self.cache_dir, "task_status.json")
            if not os.path.exists(status_file):
                return {}
                
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取状态失败: {e}")
            return {}

def create_app(log_dir: str, cache_dir: str, refresh_callback=None) -> Flask:
    """创建 Flask 应用"""
    app = Flask(__name__)
    
    # 禁用 Flask 默认日志
    app.logger.disabled = True
    log = logging.getLogger('werkzeug')
    log.disabled = True
    
    # 初始化监控器
    monitor = TaskMonitor(log_dir, cache_dir, refresh_callback)
    
    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')

    @app.route('/api/logs')
    def get_logs():
        """获取最新日志"""
        logs = monitor.get_latest_logs()
        return jsonify({"logs": logs})

    @app.route('/api/status')
    def get_status():
        """获取任务状态"""
        status = monitor.get_task_status()
        return jsonify(status)
        
    @app.route('/api/refresh', methods=['POST'])
    def refresh_files():
        """手动刷新文件列表"""
        try:
            if monitor.refresh_callback:
                result = monitor.refresh_callback()
                return jsonify({
                    "success": True,
                    "message": "刷新成功" if result else "没有新文件"
                })
            return jsonify({
                "success": False,
                "message": "刷新功能未初始化"
            })
        except Exception as e:
            logger.error(f"刷新失败: {e}")
            return jsonify({
                "success": False,
                "message": f"刷新失败: {str(e)}"
            })
    
    return app

if __name__ == '__main__':
    # 独立运行时使用默认配置
    app = create_app("logs", "cache/file_lists")
    app.run(host='0.0.0.0', port=62333) 