"""
配置管理模块
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class MinIOConfig:
    """MinIO配置类"""
    
    def __init__(self):
        self.endpoint = os.getenv('MINIO_ENDPOINT', '192.168.17.130:9000')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'veefiIZOZyobBtbalUqN')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'z3iSRyAHu0FwE3UbvcTqJ9zWUDIaukyeFG8n2MFH')
        self.bucket_name = os.getenv('MINIO_BUCKET_NAME', 'data')
        self.secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
        self.base_upload_path = os.getenv('BASE_UPLOAD_PATH', '')
    
    def get_minio_client_config(self):
        """获取MinIO客户端配置"""
        return {
            'endpoint': self.endpoint,
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'secure': self.secure
        }

# 全局配置实例
minio_config = MinIOConfig()
