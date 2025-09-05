"""
文件上传到MinIO的主要模块
"""
import os
import sys
from typing import List, Optional
from minio import Minio
from minio.error import S3Error
import logging

from config import minio_config
from utils import (
    generate_minio_object_key,
    validate_file_path,
    get_file_size,
    format_file_size
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('../log/upload.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class MinIOFileUploader:
    """MinIO文件上传器"""
    
    def __init__(self):
        """初始化MinIO客户端"""
        try:
            config = minio_config.get_minio_client_config()
            self.client = Minio(**config)
            self.bucket_name = minio_config.bucket_name
            self.base_upload_path = minio_config.base_upload_path
            logger.info(f"MinIO客户端初始化成功，连接到: {config['endpoint']}")
        except Exception as e:
            logger.error(f"MinIO客户端初始化失败: {e}")
            raise
    
    def ensure_bucket_exists(self) -> bool:
        """
        确保存储桶存在，不存在则创建
        
        Returns:
            True if成功，False if失败
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"存储桶 '{self.bucket_name}' 创建成功")
            else:
                logger.info(f"存储桶 '{self.bucket_name}' 已存在")
            return True
        except S3Error as e:
            logger.error(f"存储桶操作失败: {e}")
            return False
    
    def upload_file(self, local_file_path: str, relative_path: str) -> bool:
        """
        上传单个文件到MinIO
        
        Args:
            local_file_path: 本地文件的完整路径
            relative_path: 文件的相对路径（用于生成加密文件名）
            
        Returns:
            True if上传成功，False if失败
        """
        try:
            # 验证文件
            if not validate_file_path(local_file_path):
                logger.error(f"文件不存在或不可读: {local_file_path}")
                return False
            
            # 生成MinIO对象键名
            object_key = generate_minio_object_key(self.base_upload_path, relative_path)
            
            # 获取文件大小
            file_size = get_file_size(local_file_path)
            
            logger.info(f"开始上传文件:")
            logger.info(f"  本地路径: {local_file_path}")
            logger.info(f"  相对路径: {relative_path}")
            logger.info(f"  MinIO键名: {object_key}")
            logger.info(f"  文件大小: {format_file_size(file_size)}")
            
            # 上传文件
            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                file_path=local_file_path
            )
            
            logger.info(f"文件上传成功: {object_key}")
            return True
            
        except S3Error as e:
            logger.error(f"MinIO上传失败: {e}")
            return False
        except Exception as e:
            logger.error(f"文件上传异常: {e}")
            return False
    
    def upload_files_batch(self, file_mappings: List[tuple]) -> dict:
        """
        批量上传文件
        
        Args:
            file_mappings: 文件映射列表，每个元素为(local_path, relative_path)
            
        Returns:
            上传结果统计字典
        """
        results = {
            'total': len(file_mappings),
            'success': 0,
            'failed': 0,
            'failed_files': []
        }
        
        logger.info(f"开始批量上传 {results['total']} 个文件")
        
        for local_path, relative_path in file_mappings:
            if self.upload_file(local_path, relative_path):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['failed_files'].append((local_path, relative_path))
        
        logger.info(f"批量上传完成: 成功 {results['success']}, 失败 {results['failed']}")
        
        if results['failed'] > 0:
            logger.warning("失败的文件:")
            for local_path, relative_path in results['failed_files']:
                logger.warning(f"  {local_path} -> {relative_path}")
        
        return results
    
    def upload_directory(self, directory_path: str, base_relative_path: str = "") -> dict:
        """
        上传整个目录
        
        Args:
            directory_path: 要上传的目录路径
            base_relative_path: 基础相对路径前缀
            
        Returns:
            上传结果统计字典
        """
        if not os.path.isdir(directory_path):
            logger.error(f"目录不存在: {directory_path}")
            return {'total': 0, 'success': 0, 'failed': 0, 'failed_files': []}
        
        file_mappings = []
        
        # 遍历目录获取所有文件
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                local_path = os.path.join(root, file)
                # 计算相对路径
                rel_path = os.path.relpath(local_path, directory_path)
                if base_relative_path:
                    rel_path = os.path.join(base_relative_path, rel_path).replace('\\', '/')
                
                file_mappings.append((local_path, rel_path))
        
        return self.upload_files_batch(file_mappings)

def main():
    """主函数 - 使用示例"""
    try:
        # 创建上传器实例
        uploader = MinIOFileUploader()
        
        # 确保存储桶存在
        if not uploader.ensure_bucket_exists():
            logger.error("存储桶创建失败，程序退出")
            return
        logger.info("请根据需要调用相应的上传方法")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")

if __name__ == "__main__":
    main()
