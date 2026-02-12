import re
from datetime import datetime
from typing import List, Optional
from services.database_service import DatabaseService
from dto.import_dto import ImportResult
from dto.log_dto import ApiAccessLogData
from dto.base_dto import BaseResult
from config.settings import settings
import os

class LogParser:
    def __init__(self, log_file_path: str = None, db_connection=None):
        # 优先使用传入参数，否则使用配置
        self.log_file_path = log_file_path or settings.app.log_file_path or "logs/gitlab_access.log"
        self.db_connection = db_connection
        self.db_service = DatabaseService()
    
    def start_parsing(self) -> BaseResult:
        """启动日志解析服务"""
        print(f"Starting log parser for file: {self.log_file_path}")
        
        if not os.path.exists(self.log_file_path):
            return BaseResult.create_failure(f"Log file not found: {self.log_file_path}")
        
        try:
            result = self.parse_log()
            if result.success:
                return BaseResult.create_success(f"Successfully parsed log file: {self.log_file_path}")
            else:
                return BaseResult.create_failure(f"Failed to parse log file: {result.error}")
        except Exception as e:
            return BaseResult.create_failure(f"Error during parsing: {str(e)}")
    
    def parse_log(self) -> ImportResult:
        """解析日志文件并返回解析结果"""
        try:
            if not os.path.exists(self.log_file_path):
                return ImportResult.create_file_not_found(self.log_file_path)
            
            parsed_data = []
            
            with open(self.log_file_path, 'r', encoding='utf-8') as log_file:
                for line_number, line in enumerate(log_file, 1):
                    try:
                        parsed_line = self._parse_line(line.strip())
                        if parsed_line:
                            parsed_data.append(parsed_line)
                    except Exception as e:
                        print(f"Error parsing line {line_number}: {e}")
                        continue
            
            print(f"Successfully parsed {len(parsed_data)} log entries from file")
            
            # 保存到数据库
            if parsed_data:
                result = self.db_service.insert_logs(parsed_data, self.log_file_path)
                print(f"Database insert result: success={result.success}, message={result.message}")
                return result
            else:
                return ImportResult.create_no_data()
                
        except FileNotFoundError:
            print(f"Log file not found: {self.log_file_path}")
            return ImportResult.create_file_not_found(self.log_file_path)
        except Exception as e:
            print(f"Error parsing log file: {e}")
            return ImportResult.create_failure(str(e))
    
    def parse(self) -> ImportResult:
        """用于API调用的解析方法"""
        return self.parse_log()
    
    def parse_to_dto(self) -> List[ApiAccessLogData]:
        """解析日志文件并返回 DTO 对象列表"""
        try:
            if not os.path.exists(self.log_file_path):
                return []
            
            dto_list = []
            
            with open(self.log_file_path, 'r', encoding='utf-8') as log_file:
                for line_number, line in enumerate(log_file, 1):
                    try:
                        parsed_line = self._parse_line(line.strip())
                        if parsed_line:
                            # 创建 ApiAccessLogData DTO
                            dto = ApiAccessLogData(
                                id=0,  # 数据库会自动分配
                                access_time=parsed_line['access_time'].isoformat(),
                                client_ip=parsed_line['client_ip'],
                                http_method=parsed_line['http_method'],
                                api_path=parsed_line['api_path'],
                                http_status=parsed_line['http_status'],
                                response_size=parsed_line.get('response_size'),
                                user_agent=parsed_line.get('user_agent'),
                                response_time=parsed_line.get('response_time')
                            )
                            dto_list.append(dto)
                    except Exception as e:
                        print(f"Error parsing line {line_number} to DTO: {e}")
                        continue
            
            return dto_list
                
        except Exception as e:
            print(f"Error parsing log file to DTO: {e}")
            return []
    
    def _parse_line(self, line: str) -> Optional[dict]:
        """解析单行日志"""
        if not line.strip():
            return None
            
        try:
            # GitLab访问日志的典型格式
            # IP - user [timestamp] "METHOD /path HTTP/1.1" status size "referer" "user-agent" response_time
            pattern = r'(\S+) - (\S+) \[([^\]]+)\] "(\S+) ([^"]*)" (\d+) (\d+|-) "([^"]*)" "([^"]*)"(?:\s+(\S+))?'
            match = re.match(pattern, line)
            
            if match:
                return {
                    'client_ip': match.group(1),
                    'access_time': self._parse_timestamp(match.group(3)),
                    'http_method': match.group(4),
                    'api_path': match.group(5),
                    'http_status': int(match.group(6)),
                    'response_size': int(match.group(7)) if match.group(7) != '-' else None,
                    'user_agent': match.group(9),
                    'response_time': float(match.group(10)) if match.group(10) and match.group(10) != '-' and self._is_float(match.group(10)) else None
                }
            else:
                # 如果正则不匹配，打印日志信息但不尝试简单解析
                print(f"Unable to parse log line format: {line[:100]}...")
                return None
                
        except (IndexError, ValueError) as e:
            print(f"Error parsing line: {line}, Error: {e}")
            return None
    
    def _parse_simple_format(self, line: str) -> Optional[dict]:
        """解析简单格式的日志行"""
        try:
            # 这个函数应该处理标准的 Apache/Nginx 日志格式
            # 但实际上应该由主解析函数处理，这里只是备用
            # 如果正则表达式失败，说明日志格式不符合预期
            # 直接返回 None 让主解析函数处理
            return None
        except (IndexError, ValueError) as e:
            print(f"Error parsing simple format line: {line}, Error: {e}")
            return None
        
        return None
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """解析标准时间戳格式"""
        try:
            # 处理时区信息
            timestamp_part = timestamp_str.split()[0]
            return datetime.strptime(timestamp_part, '%d/%b/%Y:%H:%M:%S')
        except Exception as e:
            print(f"Error parsing timestamp '{timestamp_str}': {e}")
            return datetime.now()
    
    def _parse_simple_timestamp(self, timestamp_str: str) -> datetime:
        """解析简单时间戳格式"""
        try:
            # 处理 ISO 8601 格式
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except Exception as e:
            print(f"Error parsing simple timestamp '{timestamp_str}': {e}")
            return datetime.now()
    
    def _is_float(self, value: str) -> bool:
        """检查字符串是否为浮点数"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def get_parsing_stats(self) -> dict:
        """获取解析统计信息"""
        try:
            if not os.path.exists(self.log_file_path):
                return {
                    'file_exists': False,
                    'file_path': self.log_file_path,
                    'error': 'File not found'
                }
            
            # 获取文件信息
            file_stat = os.stat(self.log_file_path)
            file_size = file_stat.st_size
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
            
            # 快速统计行数
            line_count = 0
            valid_lines = 0
            
            with open(self.log_file_path, 'r', encoding='utf-8') as log_file:
                for line in log_file:
                    line_count += 1
                    if line.strip() and not line.startswith('#'):
                        valid_lines += 1
            
            return {
                'file_exists': True,
                'file_path': self.log_file_path,
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'last_modified': file_mtime.isoformat(),
                'total_lines': line_count,
                'valid_lines': valid_lines,
                'estimated_records': valid_lines
            }
            
        except Exception as e:
            return {
                'file_exists': False,
                'file_path': self.log_file_path,
                'error': str(e)
            }
    
    def validate_log_format(self, sample_lines: int = 10) -> BaseResult:
        """验证日志格式是否可以正确解析"""
        try:
            if not os.path.exists(self.log_file_path):
                return BaseResult.create_failure(f"Log file not found: {self.log_file_path}")
            
            success_count = 0
            total_count = 0
            errors = []
            
            with open(self.log_file_path, 'r', encoding='utf-8') as log_file:
                for line_number, line in enumerate(log_file, 1):
                    if total_count >= sample_lines:
                        break
                    
                    if line.strip():
                        total_count += 1
                        parsed = self._parse_line(line.strip())
                        if parsed:
                            success_count += 1
                        else:
                            errors.append(f"Line {line_number}: {line.strip()[:50]}...")
            
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            if success_rate >= 80:
                return BaseResult.create_success(
                    f"Log format validation passed. Success rate: {success_rate:.1f}% ({success_count}/{total_count})"
                )
            else:
                error_msg = f"Log format validation failed. Success rate: {success_rate:.1f}% ({success_count}/{total_count})"
                if errors:
                    error_msg += f"\nSample errors: {'; '.join(errors[:3])}"
                return BaseResult.create_failure(error_msg)
                
        except Exception as e:
            return BaseResult.create_failure(f"Error validating log format: {str(e)}")