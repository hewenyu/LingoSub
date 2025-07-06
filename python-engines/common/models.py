"""
核心业务数据模型定义
包含项目中使用的基础数据结构和枚举，使用 Pydantic 进行数据验证
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


# 基础标识类型
TaskId = str
EngineId = str
FileId = str
UserId = str


# 语言类型
class Language(str, Enum):
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"
    AUTO = "auto"


# 音频格式
class AudioFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"
    MP4 = "mp4"
    M4A = "m4a"
    FLAC = "flac"
    AAC = "aac"


# 视频格式
class VideoFormat(str, Enum):
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    WMV = "wmv"


# 文件类型
class FileType(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"


# 时间戳信息
class TimeStamp(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    start: float = Field(..., description="开始时间(秒)")
    end: float = Field(..., description="结束时间(秒)")
    text: str = Field(..., description="对应文本")
    confidence: Optional[float] = Field(None, description="置信度(0-1)")

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('confidence must be between 0 and 1')
        return v

    @field_validator('end')
    @classmethod
    def validate_end_time(cls, v, info):
        if hasattr(info, 'data') and 'start' in info.data and v <= info.data['start']:
            raise ValueError('end time must be greater than start time')
        return v


# 文件信息
class FileInfo(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    id: FileId
    name: str
    path: str
    size: int = Field(..., ge=0, description="文件大小(字节)")
    type: FileType
    format: Union[AudioFormat, VideoFormat]
    duration: Optional[float] = Field(None, description="时长(秒)")
    created_at: datetime
    modified_at: datetime
    metadata: Optional[Dict[str, Any]] = None


# 用户配置
class UserConfig(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    language: Language = Language.CHINESE_SIMPLIFIED
    theme: str = Field("light", pattern=r"^(light|dark)$")
    auto_save: bool = True
    default_engines: List[EngineId] = Field(default_factory=lambda: ["funasr"])
    output_format: str = Field("srt", pattern=r"^(srt|ass|vtt)$")
    max_concurrent_tasks: int = Field(2, ge=1, le=10)


# 系统健康状态
class SystemHealth(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU使用率(%)")
    memory_usage: float = Field(..., ge=0, le=100, description="内存使用率(%)")
    disk_usage: float = Field(..., ge=0, le=100, description="磁盘使用率(%)")
    gpu_usage: Optional[float] = Field(None, ge=0, le=100, description="GPU使用率(%)")
    status: str = Field(..., pattern=r"^(healthy|warning|error)$")
    timestamp: datetime


# 错误信息
class ErrorInfo(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    stack: Optional[str] = None


# 分页信息
class Pagination(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, le=100, description="每页大小")
    total: int = Field(..., ge=0, description="总记录数")
    total_pages: int = Field(..., ge=0, description="总页数")

    @field_validator('total_pages')
    @classmethod
    def validate_total_pages(cls, v, info):
        if hasattr(info, 'data') and 'total' in info.data and 'page_size' in info.data:
            expected_pages = (info.data['total'] + info.data['page_size'] - 1) // info.data['page_size']
            if v != expected_pages:
                raise ValueError('total_pages calculation error')
        return v


# API响应包装
class ApiResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorInfo] = None
    pagination: Optional[Pagination] = None

    @field_validator('error')
    @classmethod
    def validate_error_with_success(cls, v, info):
        if hasattr(info, 'data') and 'success' in info.data and not info.data['success'] and v is None:
            raise ValueError('error must be provided when success is False')
        return v


# 进度信息
class Progress(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)
    
    current: int = Field(..., ge=0, description="当前进度")
    total: int = Field(..., ge=0, description="总进度")
    percentage: float = Field(..., ge=0, le=100, description="完成百分比")
    estimated_remaining: Optional[int] = Field(None, ge=0, description="预计剩余时间(秒)")
    status: str = Field(..., pattern=r"^(pending|processing|completed|error)$")

    @field_validator('percentage')
    @classmethod
    def validate_percentage(cls, v, info):
        if hasattr(info, 'data') and 'current' in info.data and 'total' in info.data and info.data['total'] > 0:
            expected_percentage = (info.data['current'] / info.data['total']) * 100
            if abs(v - expected_percentage) > 0.01:  # 允许小数点误差
                raise ValueError('percentage calculation error')
        return v


# 通用响应类
class SuccessResponse(ApiResponse):
    success: bool = True
    error: Optional[ErrorInfo] = None


class ErrorResponse(ApiResponse):
    success: bool = False
    data: Optional[Any] = None

    def __init__(self, error: ErrorInfo, **data):
        super().__init__(error=error, **data) 