"""
核心业务数据模型定义
包含项目中使用的基础数据结构和枚举，使用 Pydantic 进行数据验证
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uuid


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
    words: Optional[List[Dict[str, Any]]] = Field(None, description="词级时间戳")

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

    @field_validator('start')
    @classmethod
    def validate_start_time(cls, v):
        if v < 0:
            raise ValueError('start time must be non-negative')
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


class EngineType(str, Enum):
    """引擎类型枚举"""
    FUNASR = "funasr"
    FASTER_WHISPER = "faster_whisper"
    TEST = "test"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EngineConfig(BaseModel):
    """引擎配置模型"""
    engine_id: str = Field(..., description="引擎唯一标识")
    engine_type: EngineType = Field(..., description="引擎类型")
    model_name: str = Field(..., description="使用的模型名称")
    device: str = Field(default="cpu", description="运行设备 (cpu/cuda)")
    language: str = Field(default="zh", description="语言代码")
    max_workers: int = Field(default=1, description="最大并发数")
    timeout: int = Field(default=300, description="超时时间(秒)")
    options: Dict[str, Any] = Field(default_factory=dict, description="额外选项")

    @field_validator("device")
    @classmethod
    def validate_device(cls, v):
        valid_devices = ["cpu", "cuda", "auto"]
        if v not in valid_devices:
            raise ValueError(f"Device must be one of {valid_devices}")
        return v


class TranscriptionRequest(BaseModel):
    """转录请求模型"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="任务ID")
    file_path: str = Field(..., description="音频文件路径")
    language: Optional[str] = Field(None, description="音频语言")
    format: Optional[AudioFormat] = Field(None, description="音频格式")
    priority: Priority = Field(default=Priority.NORMAL, description="任务优先级")
    options: Dict[str, Any] = Field(default_factory=dict, description="转录选项")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v):
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()


class TranscriptionResponse(BaseModel):
    """转录响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    text: str = Field(..., description="转录文本")
    timestamps: List[TimeStamp] = Field(default_factory=list, description="时间戳列表")
    confidence: float = Field(0.0, description="整体置信度")
    language: Optional[str] = Field(None, description="识别的语言")
    duration: Optional[float] = Field(None, description="音频时长(秒)")
    processing_time: Optional[float] = Field(None, description="处理时间(秒)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class EngineMetrics(BaseModel):
    """引擎指标模型"""
    engine_id: str = Field(..., description="引擎ID")
    total_requests: int = Field(default=0, description="总请求数")
    successful_requests: int = Field(default=0, description="成功请求数")
    failed_requests: int = Field(default=0, description="失败请求数")
    avg_processing_time: float = Field(default=0.0, description="平均处理时间(秒)")
    total_processing_time: float = Field(default=0.0, description="总处理时间(秒)")
    memory_usage: float = Field(default=0.0, description="内存使用量(MB)")
    cpu_usage: float = Field(default=0.0, description="CPU使用率(%)")
    last_updated: datetime = Field(default_factory=datetime.now, description="更新时间")

    def increment_request(self):
        """增加请求计数"""
        self.total_requests += 1
        self.last_updated = datetime.now()

    def increment_success(self, processing_time: float = 0.0):
        """增加成功计数"""
        self.successful_requests += 1
        self.total_processing_time += processing_time
        if self.successful_requests > 0:
            self.avg_processing_time = self.total_processing_time / self.successful_requests
        self.last_updated = datetime.now()

    def increment_error(self):
        """增加错误计数"""
        self.failed_requests += 1
        self.last_updated = datetime.now()


class HealthStatus(BaseModel):
    """健康状态模型"""
    status: str = Field(..., description="状态: healthy/unhealthy/error")
    engine_id: str = Field(..., description="引擎ID")
    uptime: float = Field(..., description="运行时间(秒)")
    last_heartbeat: datetime = Field(..., description="最后心跳时间")
    metrics: EngineMetrics = Field(..., description="引擎指标")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["healthy", "unhealthy", "error"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class SidecarCommand(BaseModel):
    """Sidecar 命令模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="命令ID")
    type: str = Field(..., description="命令类型")
    payload: Dict[str, Any] = Field(default_factory=dict, description="命令负载")
    timeout: Optional[int] = Field(None, description="超时时间(秒)")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class SidecarResponse(BaseModel):
    """Sidecar 响应模型"""
    id: str = Field(..., description="对应命令ID")
    status: str = Field(..., description="响应状态: success/error")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误信息")
    error_type: Optional[str] = Field(None, description="错误类型")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["success", "error"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class ProcessInfo(BaseModel):
    """进程信息模型"""
    process_id: str = Field(..., description="进程ID")
    engine_type: EngineType = Field(..., description="引擎类型")
    pid: Optional[int] = Field(None, description="系统进程ID")
    status: str = Field(..., description="进程状态")
    start_time: datetime = Field(..., description="启动时间")
    last_heartbeat: datetime = Field(..., description="最后心跳")
    metrics: EngineMetrics = Field(..., description="进程指标")
    config: EngineConfig = Field(..., description="引擎配置")


class BatchRequest(BaseModel):
    """批量请求模型"""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="批次ID")
    requests: List[TranscriptionRequest] = Field(..., description="请求列表")
    priority: Priority = Field(default=Priority.NORMAL, description="批次优先级")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="批次元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    @field_validator("requests")
    @classmethod
    def validate_requests(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Requests list cannot be empty")
        return v


class BatchResponse(BaseModel):
    """批量响应模型"""
    batch_id: str = Field(..., description="批次ID")
    status: TaskStatus = Field(..., description="批次状态")
    responses: List[TranscriptionResponse] = Field(..., description="响应列表")
    total_requests: int = Field(..., description="总请求数")
    successful_requests: int = Field(..., description="成功请求数")
    failed_requests: int = Field(..., description="失败请求数")
    total_processing_time: float = Field(..., description="总处理时间")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


# 类型别名
RequestType = Union[TranscriptionRequest, BatchRequest]
ResponseType = Union[TranscriptionResponse, BatchResponse] 