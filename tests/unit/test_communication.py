"""
Tests for SidecarCommunicator
SidecarCommunicator 通信模块的单元测试
"""

import pytest
import asyncio
import json
import io
import sys
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../python-engines'))

from common.communication import SidecarCommunicator, JsonRpcProtocol, StreamCommunicator
from common.models import SidecarCommand, SidecarResponse


class TestSidecarCommunicator:
    """SidecarCommunicator 测试类"""
    
    @pytest.fixture
    def mock_command_handler(self):
        """模拟命令处理器"""
        async def handler(command_data):
            if command_data.get("type") == "test":
                return {"result": "success", "data": command_data.get("payload", {})}
            elif command_data.get("type") == "error":
                raise ValueError("Test error")
            else:
                return {"result": "unknown"}
        
        return handler
    
    @pytest.fixture
    def communicator(self, mock_command_handler):
        """创建通信器实例"""
        return SidecarCommunicator(mock_command_handler)
    
    def test_communicator_initialization(self, communicator):
        """测试通信器初始化"""
        assert communicator.command_handler is not None
        assert communicator.running == False
        assert communicator.loop is None
    
    @pytest.mark.asyncio
    async def test_send_json(self, communicator):
        """测试 JSON 发送"""
        test_data = {"type": "test", "message": "hello"}
        
        with patch('builtins.print') as mock_print:
            await communicator._send_json(test_data)
            
            # 验证调用
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            
            # 解析 JSON 并验证
            parsed = json.loads(call_args)
            assert parsed["type"] == "test"
            assert parsed["message"] == "hello"
    
    @pytest.mark.asyncio
    async def test_send_response(self, communicator):
        """测试发送响应"""
        with patch.object(communicator, '_send_json') as mock_send:
            await communicator._send_response("test-id", "success", {"result": "ok"})
            
            mock_send.assert_called_once()
            response_data = mock_send.call_args[0][0]
            
            assert response_data["id"] == "test-id"
            assert response_data["status"] == "success"
            assert response_data["data"]["result"] == "ok"
    
    @pytest.mark.asyncio
    async def test_send_error_response(self, communicator):
        """测试发送错误响应"""
        with patch.object(communicator, '_send_json') as mock_send:
            await communicator._send_error_response("test-id", "Test error", "ValueError")
            
            mock_send.assert_called_once()
            response_data = mock_send.call_args[0][0]
            
            assert response_data["id"] == "test-id"
            assert response_data["status"] == "error"
            assert response_data["error"] == "Test error"
            assert response_data["error_type"] == "ValueError"
    
    @pytest.mark.asyncio
    async def test_handle_command_success(self, communicator):
        """测试成功处理命令"""
        command = SidecarCommand(
            type="test",
            payload={"data": "test_data"}
        )
        
        with patch.object(communicator, '_send_response') as mock_send:
            await communicator._handle_command(command)
            
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            assert args[0] == command.id  # command_id
            assert args[1] == "success"   # status
    
    @pytest.mark.asyncio
    async def test_handle_command_error(self, communicator):
        """测试处理命令错误"""
        command = SidecarCommand(
            type="error",
            payload={}
        )
        
        with patch.object(communicator, '_send_error_response') as mock_send:
            await communicator._handle_command(command)
            
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            assert args[0] == command.id  # command_id
            assert "Test error" in args[1]  # error message
    
    @pytest.mark.asyncio
    async def test_handle_command_timeout(self, communicator):
        """测试命令超时"""
        async def slow_handler(command_data):
            await asyncio.sleep(2)  # 模拟慢处理
            return {"result": "slow"}
        
        slow_communicator = SidecarCommunicator(slow_handler)
        
        command = SidecarCommand(
            type="slow",
            timeout=0.1  # 0.1秒超时
        )
        
        with patch.object(slow_communicator, '_send_error_response') as mock_send:
            await slow_communicator._handle_command(command)
            
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            assert args[0] == command.id
            assert "timed out" in args[1].lower()
    
    @pytest.mark.asyncio
    async def test_send_notification(self, communicator):
        """测试发送通知"""
        with patch.object(communicator, '_send_json') as mock_send:
            await communicator.send_notification("status_update", {"status": "running"})
            
            mock_send.assert_called_once()
            notification_data = mock_send.call_args[0][0]
            
            assert notification_data["type"] == "notification"
            assert notification_data["notification_type"] == "status_update"
            assert notification_data["data"]["status"] == "running"
            assert "timestamp" in notification_data
    
    @pytest.mark.asyncio
    async def test_send_heartbeat(self, communicator):
        """测试发送心跳"""
        with patch.object(communicator, '_send_json') as mock_send:
            await communicator.send_heartbeat("engine-123", "healthy")
            
            mock_send.assert_called_once()
            heartbeat_data = mock_send.call_args[0][0]
            
            assert heartbeat_data["type"] == "heartbeat"
            assert heartbeat_data["engine_id"] == "engine-123"
            assert heartbeat_data["status"] == "healthy"
            assert "timestamp" in heartbeat_data


class TestJsonRpcProtocol:
    """JsonRpcProtocol 测试类"""
    
    def test_create_request(self):
        """测试创建 JSON-RPC 请求"""
        request = JsonRpcProtocol.create_request(
            method="transcribe",
            params={"file": "test.wav"},
            request_id="123"
        )
        
        assert request["jsonrpc"] == "2.0"
        assert request["method"] == "transcribe"
        assert request["params"]["file"] == "test.wav"
        assert request["id"] == "123"
    
    def test_create_request_without_id(self):
        """测试创建无ID的请求（通知）"""
        request = JsonRpcProtocol.create_request(
            method="notify",
            params={"message": "hello"}
        )
        
        assert request["jsonrpc"] == "2.0"
        assert request["method"] == "notify"
        assert "id" not in request
    
    def test_create_response(self):
        """测试创建 JSON-RPC 响应"""
        response = JsonRpcProtocol.create_response(
            result={"transcription": "hello"},
            request_id="123"
        )
        
        assert response["jsonrpc"] == "2.0"
        assert response["result"]["transcription"] == "hello"
        assert response["id"] == "123"
    
    def test_create_error_response(self):
        """测试创建错误响应"""
        response = JsonRpcProtocol.create_error_response(
            error_code=-32602,
            error_message="Invalid params",
            request_id="123"
        )
        
        assert response["jsonrpc"] == "2.0"
        assert response["error"]["code"] == -32602
        assert response["error"]["message"] == "Invalid params"
        assert response["id"] == "123"
    
    def test_parse_request(self):
        """测试解析请求"""
        data = {
            "jsonrpc": "2.0",
            "method": "transcribe",
            "params": {"file": "test.wav"},
            "id": "123"
        }
        
        method, params, request_id = JsonRpcProtocol.parse_request(data)
        
        assert method == "transcribe"
        assert params["file"] == "test.wav"
        assert request_id == "123"
    
    def test_parse_request_invalid_version(self):
        """测试解析无效版本的请求"""
        data = {
            "jsonrpc": "1.0",
            "method": "test"
        }
        
        with pytest.raises(ValueError, match="Invalid JSON-RPC version"):
            JsonRpcProtocol.parse_request(data)
    
    def test_parse_request_missing_method(self):
        """测试解析缺少方法的请求"""
        data = {
            "jsonrpc": "2.0",
            "params": {}
        }
        
        with pytest.raises(ValueError, match="Missing method in request"):
            JsonRpcProtocol.parse_request(data)


class TestStreamCommunicator:
    """StreamCommunicator 测试类"""
    
    @pytest.fixture
    def stream_communicator(self):
        """创建流通信器"""
        return StreamCommunicator(chunk_size=100)
    
    def test_stream_communicator_init(self, stream_communicator):
        """测试流通信器初始化"""
        assert stream_communicator.chunk_size == 100
    
    @pytest.mark.asyncio
    async def test_send_stream(self, stream_communicator):
        """测试发送流数据"""
        test_data = b"Hello, this is test stream data that should be split into chunks."
        stream_id = "test-stream-001"
        
        with patch('builtins.print') as mock_print:
            await stream_communicator.send_stream(test_data, stream_id)
            
            # 验证调用次数：header + chunks + footer
            # 数据长度 66 字节，chunk_size 100，所以应该有 1 个chunk
            expected_calls = 3  # header, 1 chunk, footer
            assert mock_print.call_count == expected_calls
            
            # 验证 header
            header_call = json.loads(mock_print.call_args_list[0][0][0])
            assert header_call["type"] == "stream_start"
            assert header_call["stream_id"] == stream_id
            assert header_call["total_size"] == len(test_data)
            
            # 验证 chunk
            chunk_call = json.loads(mock_print.call_args_list[1][0][0])
            assert chunk_call["type"] == "stream_chunk"
            assert chunk_call["stream_id"] == stream_id
            assert chunk_call["offset"] == 0
            
            # 验证 footer
            footer_call = json.loads(mock_print.call_args_list[2][0][0])
            assert footer_call["type"] == "stream_end"
            assert footer_call["stream_id"] == stream_id
    
    @pytest.mark.asyncio
    async def test_send_large_stream(self, stream_communicator):
        """测试发送大数据流"""
        # 创建大于 chunk_size 的数据
        test_data = b"x" * 250  # 250 字节，chunk_size 是 100
        stream_id = "large-stream"
        
        with patch('builtins.print') as mock_print:
            await stream_communicator.send_stream(test_data, stream_id)
            
            # 应该有：header + 3 chunks + footer = 5 calls
            assert mock_print.call_count == 5
            
            # 验证所有chunk调用
            chunk_calls = [
                json.loads(call[0][0]) 
                for call in mock_print.call_args_list[1:-1]  # 除去header和footer
                if json.loads(call[0][0])["type"] == "stream_chunk"
            ]
            
            assert len(chunk_calls) == 3
            
            # 验证偏移量
            expected_offsets = [0, 100, 200]
            actual_offsets = [call["offset"] for call in chunk_calls]
            assert actual_offsets == expected_offsets


class TestModelValidation:
    """模型验证测试"""
    
    def test_sidecar_command_validation(self):
        """测试 SidecarCommand 验证"""
        # 有效命令
        command = SidecarCommand(
            type="transcribe",
            payload={"file": "test.wav"}
        )
        
        assert command.type == "transcribe"
        assert command.payload["file"] == "test.wav"
        assert command.id is not None
        assert isinstance(command.created_at, datetime)
    
    def test_sidecar_response_validation(self):
        """测试 SidecarResponse 验证"""
        # 成功响应
        response = SidecarResponse(
            id="test-123",
            status="success",
            data={"result": "ok"}
        )
        
        assert response.id == "test-123"
        assert response.status == "success"
        assert response.data["result"] == "ok"
        assert response.error is None
    
    def test_sidecar_response_invalid_status(self):
        """测试无效状态的响应"""
        with pytest.raises(ValueError, match="Status must be one of"):
            SidecarResponse(
                id="test",
                status="invalid_status"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 