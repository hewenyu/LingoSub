"""
Configuration Management System
配置管理系统，支持环境变量和配置文件
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, Type, TypeVar, Union
from pathlib import Path
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .models import EngineConfig, EngineType


T = TypeVar('T')


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "lingosub"
    username: str = "postgres"
    password: str = ""
    max_connections: int = 10


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True


@dataclass
class PerformanceConfig:
    """性能配置"""
    max_workers: int = 4
    timeout: int = 300
    memory_limit: int = 2048  # MB
    cpu_limit: float = 0.8  # 80%
    batch_size: int = 1
    queue_size: int = 100


@dataclass
class SecurityConfig:
    """安全配置"""
    enable_auth: bool = False
    secret_key: str = ""
    token_expiry: int = 3600  # 1小时
    allowed_origins: list = field(default_factory=list)
    rate_limit: int = 100  # 请求/分钟


@dataclass
class SidecarConfig:
    """Sidecar 配置"""
    # 基础配置
    engine_id: str = "default"
    engine_type: EngineType = EngineType.TEST
    model_name: str = "default"
    device: str = "cpu"
    language: str = "zh"
    
    # 性能配置
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # 日志配置
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # 安全配置
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # 数据库配置
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # 扩展配置
    extensions: Dict[str, Any] = field(default_factory=dict)


class ConfigSource(ABC):
    """配置源抽象基类"""
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """加载配置"""
        pass
    
    @abstractmethod
    def exists(self) -> bool:
        """检查配置源是否存在"""
        pass


class FileConfigSource(ConfigSource):
    """文件配置源"""
    
    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.logger = logging.getLogger("config.file")
    
    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.exists():
            return {}
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                if self.file_path.suffix.lower() == '.json':
                    return json.load(f)
                elif self.file_path.suffix.lower() in ['.yml', '.yaml']:
                    return yaml.safe_load(f) or {}
                else:
                    raise ValueError(f"Unsupported file format: {self.file_path.suffix}")
        except Exception as e:
            self.logger.error(f"Error loading config file {self.file_path}: {str(e)}")
            return {}
    
    def exists(self) -> bool:
        """检查文件是否存在"""
        return self.file_path.exists() and self.file_path.is_file()


class EnvironmentConfigSource(ConfigSource):
    """环境变量配置源"""
    
    def __init__(self, prefix: str = "LINGOSUB_"):
        self.prefix = prefix
        self.logger = logging.getLogger("config.env")
    
    def load(self) -> Dict[str, Any]:
        """加载环境变量配置"""
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                # 移除前缀并转换为配置键
                config_key = key[len(self.prefix):].lower()
                
                # 尝试解析值
                try:
                    # 尝试 JSON 解析
                    if value.startswith(('[', '{')):
                        config[config_key] = json.loads(value)
                    # 布尔值
                    elif value.lower() in ['true', 'false']:
                        config[config_key] = value.lower() == 'true'
                    # 数字
                    elif value.isdigit():
                        config[config_key] = int(value)
                    elif self._is_float(value):
                        config[config_key] = float(value)
                    # 字符串
                    else:
                        config[config_key] = value
                except Exception as e:
                    self.logger.warning(f"Error parsing env var {key}: {str(e)}")
                    config[config_key] = value
        
        return config
    
    def exists(self) -> bool:
        """检查是否存在相关环境变量"""
        return any(key.startswith(self.prefix) for key in os.environ.keys())
    
    def _is_float(self, value: str) -> bool:
        """检查是否为浮点数"""
        try:
            float(value)
            return True
        except ValueError:
            return False


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_class: Type[T] = SidecarConfig):
        self.config_class = config_class
        self.config_sources = []
        self.logger = logging.getLogger("config.manager")
        self._config = None
    
    def add_source(self, source: ConfigSource):
        """添加配置源"""
        self.config_sources.append(source)
    
    def load(self) -> T:
        """加载配置"""
        if self._config is not None:
            return self._config
        
        # 合并所有配置源
        merged_config = {}
        
        for source in self.config_sources:
            try:
                if source.exists():
                    source_config = source.load()
                    merged_config.update(source_config)
                    self.logger.debug(f"Loaded config from {type(source).__name__}")
            except Exception as e:
                self.logger.error(f"Error loading from {type(source).__name__}: {str(e)}")
        
        # 创建配置对象
        try:
            self._config = self._create_config(merged_config)
            self.logger.info("Configuration loaded successfully")
            return self._config
        except Exception as e:
            self.logger.error(f"Error creating config object: {str(e)}")
            # 返回默认配置
            self._config = self.config_class()
            return self._config
    
    def _create_config(self, data: Dict[str, Any]) -> T:
        """创建配置对象"""
        if self.config_class == SidecarConfig:
            return self._create_sidecar_config(data)
        else:
            # 对于其他配置类型，尝试直接创建
            return self.config_class(**data)
    
    def _create_sidecar_config(self, data: Dict[str, Any]) -> SidecarConfig:
        """创建 Sidecar 配置"""
        config = SidecarConfig()
        
        # 基础配置
        config.engine_id = data.get("engine_id", config.engine_id)
        config.engine_type = EngineType(data.get("engine_type", config.engine_type.value))
        config.model_name = data.get("model_name", config.model_name)
        config.device = data.get("device", config.device)
        config.language = data.get("language", config.language)
        
        # 性能配置
        if "performance" in data:
            perf_data = data["performance"]
            config.performance = PerformanceConfig(
                max_workers=perf_data.get("max_workers", config.performance.max_workers),
                timeout=perf_data.get("timeout", config.performance.timeout),
                memory_limit=perf_data.get("memory_limit", config.performance.memory_limit),
                cpu_limit=perf_data.get("cpu_limit", config.performance.cpu_limit),
                batch_size=perf_data.get("batch_size", config.performance.batch_size),
                queue_size=perf_data.get("queue_size", config.performance.queue_size),
            )
        
        # 日志配置
        if "logging" in data:
            log_data = data["logging"]
            config.logging = LoggingConfig(
                level=log_data.get("level", config.logging.level),
                format=log_data.get("format", config.logging.format),
                file_path=log_data.get("file_path", config.logging.file_path),
                max_file_size=log_data.get("max_file_size", config.logging.max_file_size),
                backup_count=log_data.get("backup_count", config.logging.backup_count),
                console_output=log_data.get("console_output", config.logging.console_output),
            )
        
        # 安全配置
        if "security" in data:
            sec_data = data["security"]
            config.security = SecurityConfig(
                enable_auth=sec_data.get("enable_auth", config.security.enable_auth),
                secret_key=sec_data.get("secret_key", config.security.secret_key),
                token_expiry=sec_data.get("token_expiry", config.security.token_expiry),
                allowed_origins=sec_data.get("allowed_origins", config.security.allowed_origins),
                rate_limit=sec_data.get("rate_limit", config.security.rate_limit),
            )
        
        # 数据库配置
        if "database" in data:
            db_data = data["database"]
            config.database = DatabaseConfig(
                host=db_data.get("host", config.database.host),
                port=db_data.get("port", config.database.port),
                database=db_data.get("database", config.database.database),
                username=db_data.get("username", config.database.username),
                password=db_data.get("password", config.database.password),
                max_connections=db_data.get("max_connections", config.database.max_connections),
            )
        
        # 扩展配置
        config.extensions = data.get("extensions", config.extensions)
        
        return config
    
    def get_engine_config(self) -> EngineConfig:
        """获取引擎配置"""
        config = self.load()
        
        return EngineConfig(
            engine_id=config.engine_id,
            engine_type=config.engine_type,
            model_name=config.model_name,
            device=config.device,
            language=config.language,
            max_workers=config.performance.max_workers,
            timeout=config.performance.timeout,
            options=config.extensions
        )
    
    def validate(self) -> bool:
        """验证配置"""
        try:
            config = self.load()
            
            # 验证引擎类型
            if config.engine_type not in EngineType:
                raise ValueError(f"Invalid engine type: {config.engine_type}")
            
            # 验证设备
            if config.device not in ["cpu", "cuda", "auto"]:
                raise ValueError(f"Invalid device: {config.device}")
            
            # 验证性能配置
            if config.performance.max_workers <= 0:
                raise ValueError("max_workers must be positive")
            
            if config.performance.timeout <= 0:
                raise ValueError("timeout must be positive")
            
            # 验证日志级别
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config.logging.level not in valid_levels:
                raise ValueError(f"Invalid log level: {config.logging.level}")
            
            self.logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {str(e)}")
            return False
    
    def save(self, file_path: Union[str, Path], format: str = "json"):
        """保存配置到文件"""
        config = self.load()
        file_path = Path(file_path)
        
        try:
            # 创建目录
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 序列化配置
            if format == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config_to_dict(config), f, indent=2, ensure_ascii=False)
            elif format == "yaml":
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self._config_to_dict(config), f, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Configuration saved to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            raise
    
    def _config_to_dict(self, config: T) -> Dict[str, Any]:
        """配置对象转字典"""
        if hasattr(config, '__dict__'):
            result = {}
            for key, value in config.__dict__.items():
                if hasattr(value, '__dict__'):
                    result[key] = self._config_to_dict(value)
                else:
                    result[key] = value
            return result
        return config


def create_default_config_manager() -> ConfigManager:
    """创建默认配置管理器"""
    manager = ConfigManager()
    
    # 添加配置源（优先级从低到高）
    manager.add_source(FileConfigSource("config.yaml"))
    manager.add_source(FileConfigSource("config.json"))
    manager.add_source(EnvironmentConfigSource())
    
    return manager


def load_config(config_file: Optional[str] = None) -> SidecarConfig:
    """加载配置的便捷函数"""
    manager = ConfigManager()
    
    if config_file:
        manager.add_source(FileConfigSource(config_file))
    
    # 默认配置源
    manager.add_source(EnvironmentConfigSource())
    
    return manager.load() 