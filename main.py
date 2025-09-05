"""
主程序入口 - MinIO文件上传工具
"""
import argparse
import sys
import os
from config.file_uploader import MinIOFileUploader
import logging

logger = logging.getLogger(__name__)

def upload_single_file(uploader: MinIOFileUploader, file_path: str, relative_path: str):
    """上传单个文件"""
    print(f"正在上传单个文件...")
    print(f"本地路径: {file_path}")
    print(f"相对路径: {relative_path}")
    
    success = uploader.upload_file(file_path, relative_path)
    if success:
        print("文件上传成功!")
    else:
        print("文件上传失败!")
    return success

def upload_multiple_files(uploader: MinIOFileUploader, file_mappings: list):
    """批量上传文件"""
    print(f"正在批量上传 {len(file_mappings)} 个文件...")
    results = uploader.upload_files_batch(file_mappings)
    print(f"\n📊 上传结果统计:")
    print(f"总文件数: {results['total']}")
    print(f"成功: {results['success']}")
    print(f"失败: {results['failed']}")
    
    if results['failed'] > 0:
        print(f"\n失败的文件:")
        for local_path, relative_path in results['failed_files']:
            print(f"  {local_path} -> {relative_path}")
    
    return results['failed'] == 0

def upload_directory(uploader: MinIOFileUploader, dir_path: str, base_relative: str = ""):
    """上传整个目录"""
    print(f"正在上传目录: {dir_path}")
    if base_relative:
        print(f"基础相对路径: {base_relative}")
    
    results = uploader.upload_directory(dir_path, base_relative)
    
    print(f"\n📊 目录上传结果统计:")
    print(f"总文件数: {results['total']}")
    print(f"成功: {results['success']}")
    print(f"失败: {results['failed']}")
    
    if results['failed'] > 0:
        print(f"\n失败的文件:")
        for local_path, relative_path in results['failed_files']:
            print(f"  {local_path} -> {relative_path}")
    
    return results['failed'] == 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MinIO文件上传工具')
    parser.add_argument('--mode', choices=['single', 'batch', 'directory'], 
                       default='single', help='上传模式')
    parser.add_argument('--file', help='单个文件路径')
    parser.add_argument('--relative', help='文件相对路径（用于生成加密文件名）')
    parser.add_argument('--directory', help='要上传的目录路径')
    parser.add_argument('--base-relative', default='', help='目录上传时的基础相对路径')
    parser.add_argument('--files', nargs='+', help='批量上传的文件列表，格式: local_path:relative_path')
    
    args = parser.parse_args()
    
    try:
        print("初始化MinIO文件上传器...")
        uploader = MinIOFileUploader()
        
        print("检查存储桶...")
        if not uploader.ensure_bucket_exists():
            print("存储桶创建失败，程序退出")
            return False
        
        success = False
        
        if args.mode == 'single':
            if not args.file or not args.relative:
                print("单文件模式需要指定 --file 和 --relative 参数")
                print("示例: python main.py --mode single --file /path/to/file.txt --relative documents/file.txt")
                return False
            
            if not os.path.exists(args.file):
                print(f"文件不存在: {args.file}")
                return False
                
            success = upload_single_file(uploader, args.file, args.relative)
            
        elif args.mode == 'batch':
            if not args.files:
                print("批量模式需要指定 --files 参数")
                print("示例: python main.py --mode batch --files /path/file1.txt:docs/file1.txt /path/file2.jpg:images/file2.jpg")
                return False
            
            file_mappings = []
            for file_mapping in args.files:
                try:
                    local_path, relative_path = file_mapping.split(':', 1)
                    if not os.path.exists(local_path):
                        print(f"文件不存在，跳过: {local_path}")
                        continue
                    file_mappings.append((local_path, relative_path))
                except ValueError:
                    print(f"文件映射格式错误: {file_mapping}")
                    print("正确格式: local_path:relative_path")
                    return False
            
            if not file_mappings:
                print("没有有效的文件可上传")
                return False
                
            success = upload_multiple_files(uploader, file_mappings)
            
        elif args.mode == 'directory':
            if not args.directory:
                print("目录模式需要指定 --directory 参数")
                print("示例: python main.py --mode directory --directory /path/to/directory --base-relative backup")
                return False
            
            if not os.path.isdir(args.directory):
                print(f" 目录不存在: {args.directory}")
                return False
                
            success = upload_directory(uploader, args.directory, args.base_relative)
        
        if success:
            print("\n 所有文件上传完成!")
        else:
            print("\n部分或全部文件上传失败")
            
        return success
        
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        return False
    except Exception as e:
        print(f"\n程序执行异常: {e}")
        logger.exception("程序执行异常")
        return False

def show_usage_examples():
    """显示使用示例"""
    print("""
使用示例:
1. 上传单个文件:
   python main.py --mode single --file C:\\data\\document.pdf --relative documents/report.pdf
2. 批量上传文件:
   python main.py --mode batch --files C:\\data\\file1.txt:docs/file1.txt C:\\data\\file2.jpg:images/file2.jpg
3. 上传整个目录:
   python main.py --mode directory --directory C:\\data\\photos --base-relative backup/photos
4. 上传目录到根路径:
   python main.py --mode directory --directory C:\\data\\documents
说明:
- 文件会按当前日期自动分区 (如: 20250904)
- 文件名会根据相对路径进行MD5加密
- 所有配置通过 .env 文件管理
- 上传日志保存在 upload.log 文件中
    """)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        show_usage_examples()
    else:
        success = main()
        sys.exit(0 if success else 1)
