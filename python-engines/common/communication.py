"""
Sidecar Process Communication Module
Sidecar 进程通信模块，实现基于 stdin/stdout 的 JSON-RPC 通信
"""

import sys
import json
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime
import traceback
import signal

from .models import SidecarCommand, SidecarResponse


class SidecarCommunicator:
    """
    Sidecar 进程通信器
    处理与 Tauri 后端的双向通信
    """
    
    def __init__(self, command_handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]):
        """
        初始化通信器
        
        Args:
            command_handler: 命令处理函数
        """
        self.command_handler = command_handler
        self.logger = logging.getLogger("sidecar.communicator")
        self.running = False
        self.loop = None
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.loop:
            self.loop.stop()
    
    async def start(self):
        """启动通信循环"""
        self.running = True
        self.loop = asyncio.get_event_loop()
        self.logger.info("Sidecar communicator started")
        
        try:
            await self._listen_for_commands()
        except Exception as e:
            self.logger.error(f"Communication error: {str(e)}")
            raise
        finally:
            self.running = False
            self.logger.info("Sidecar communicator stopped")
    
    def stop(self):
        """停止通信循环"""
        self.running = False
        if self.loop:
            self.loop.stop()
    
    async def _listen_for_commands(self):
        """监听命令输入"""
        while self.running:
            try:
                # 从 stdin 读取命令
                line = await self._read_stdin()
                if not line:
                    continue
                
                # 解析命令
                try:
                    command_data = json.loads(line)
                    command = SidecarCommand(**command_data)
                except (json.JSONDecodeError, ValueError) as e:
                    self.logger.error(f"Invalid command format: {str(e)}")
                    await self._send_error_response(
                        command_id="unknown",
                        error=f"Invalid command format: {str(e)}"
                    )
                    continue
                
                # 处理命令
                await self._handle_command(command)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in command loop: {str(e)}")
                await asyncio.sleep(0.1)  # 短暂休息避免快速循环
    
    async def _read_stdin(self) -> Optional[str]:
        """异步读取 stdin"""
        try:
            loop = asyncio.get_event_loop()
            line = await loop.run_in_executor(None, sys.stdin.readline)
            return line.strip() if line else None
        except Exception as e:
            self.logger.error(f"Error reading stdin: {str(e)}")
            return None
    
    async def _handle_command(self, command: SidecarCommand):
        """处理单个命令"""
        start_time = datetime.now()
        
        try:
            self.logger.debug(f"Handling command: {command.type} (ID: {command.id})")
            
            # 检查超时
            if command.timeout:
                response_data = await asyncio.wait_for(
                    self.command_handler(command.model_dump()),
                    timeout=command.timeout
                )
            else:
                response_data = await self.command_handler(command.model_dump())
            
            # 发送成功响应
            await self._send_response(
                command_id=command.id,
                status="success",
                data=response_data
            )
            
            # 记录处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.debug(f"Command {command.id} processed in {processing_time:.3f}s")
            
        except asyncio.TimeoutError:
            self.logger.error(f"Command {command.id} timed out")
            await self._send_error_response(
                command_id=command.id,
                error="Command execution timed out",
                error_type="TimeoutError"
            )
        except Exception as e:
            self.logger.error(f"Error handling command {command.id}: {str(e)}")
            await self._send_error_response(
                command_id=command.id,
                error=str(e),
                error_type=type(e).__name__
            )
    
    async def _send_response(self, command_id: str, status: str, data: Optional[Dict[str, Any]] = None):
        """发送响应"""
        response = SidecarResponse(
            id=command_id,
            status=status,
            data=data
        )
        
        await self._send_json(response.model_dump())
    
    async def _send_error_response(self, command_id: str, error: str, error_type: str = "Error"):
        """发送错误响应"""
        response = SidecarResponse(
            id=command_id,
            status="error",
            error=error,
            error_type=error_type
        )
        
        await self._send_json(response.model_dump())
    
    async def _send_json(self, data: Dict[str, Any]):
        """发送 JSON 数据到 stdout"""
        try:
            json_str = json.dumps(data, default=str, ensure_ascii=False)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._write_stdout, json_str)
        except Exception as e:
            self.logger.error(f"Error sending JSON: {str(e)}")
    
    def _write_stdout(self, data: str):
        """同步写入 stdout"""
        try:
            print(data, flush=True)
        except Exception as e:
            self.logger.error(f"Error writing to stdout: {str(e)}")
    
    async def send_notification(self, notification_type: str, data: Dict[str, Any]):
        """发送通知 (主动推送)"""
        notification = {
            "type": "notification",
            "notification_type": notification_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_json(notification)
    
    async def send_heartbeat(self, engine_id: str, status: str):
        """发送心跳"""
        heartbeat = {
            "type": "heartbeat",
            "engine_id": engine_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_json(heartbeat)


class JsonRpcProtocol:
    """JSON-RPC 协议处理器"""
    
    @staticmethod
    def create_request(method: str, params: Dict[str, Any], request_id: str = None) -> Dict[str, Any]:
        """创建 JSON-RPC 请求"""
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        
        if request_id:
            request["id"] = request_id
        
        return request
    
    @staticmethod
    def create_response(result: Any, request_id: str) -> Dict[str, Any]:
        """创建 JSON-RPC 响应"""
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }
    
    @staticmethod
    def create_error_response(error_code: int, error_message: str, request_id: str) -> Dict[str, Any]:
        """创建 JSON-RPC 错误响应"""
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": error_code,
                "message": error_message
            },
            "id": request_id
        }
    
    @staticmethod
    def parse_request(data: Dict[str, Any]) -> tuple[str, Dict[str, Any], Optional[str]]:
        """解析 JSON-RPC 请求"""
        if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            raise ValueError("Invalid JSON-RPC version")
        
        if "method" not in data:
            raise ValueError("Missing method in request")
        
        method = data["method"]
        params = data.get("params", {})
        request_id = data.get("id")
        
        return method, params, request_id


class StreamCommunicator:
    """流式通信器 (支持大数据传输)"""
    
    def __init__(self, chunk_size: int = 8192):
        """
        初始化流式通信器
        
        Args:
            chunk_size: 数据块大小
        """
        self.chunk_size = chunk_size
        self.logger = logging.getLogger("sidecar.stream")
    
    async def send_stream(self, data: bytes, stream_id: str):
        """发送流式数据"""
        try:
            # 发送流开始信号
            await self._send_stream_header(stream_id, len(data))
            
            # 分块发送数据
            for i in range(0, len(data), self.chunk_size):
                chunk = data[i:i + self.chunk_size]
                await self._send_stream_chunk(stream_id, chunk, i)
            
            # 发送流结束信号
            await self._send_stream_footer(stream_id)
            
        except Exception as e:
            self.logger.error(f"Error sending stream {stream_id}: {str(e)}")
            raise
    
    async def _send_stream_header(self, stream_id: str, total_size: int):
        """发送流头部"""
        header = {
            "type": "stream_start",
            "stream_id": stream_id,
            "total_size": total_size,
            "timestamp": datetime.now().isoformat()
        }
        
        print(json.dumps(header), flush=True)
    
    async def _send_stream_chunk(self, stream_id: str, chunk: bytes, offset: int):
        """发送数据块"""
        import base64
        
        chunk_data = {
            "type": "stream_chunk",
            "stream_id": stream_id,
            "offset": offset,
            "size": len(chunk),
            "data": base64.b64encode(chunk).decode("utf-8")
        }
        
        print(json.dumps(chunk_data), flush=True)
    
    async def _send_stream_footer(self, stream_id: str):
        """发送流尾部"""
        footer = {
            "type": "stream_end",
            "stream_id": stream_id,
            "timestamp": datetime.now().isoformat()
        }
        
        print(json.dumps(footer), flush=True) 