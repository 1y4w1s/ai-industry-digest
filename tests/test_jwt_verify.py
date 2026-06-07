"""
Signal - JWT 验证测试
测试 token 验证逻辑

运行: python -m pytest tests/test_jwt_verify.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock, patch
import pytest


class TestJWTVerify:
    """JWT 验证测试"""

    def test_verify_token_empty(self):
        """空 token 应返回 None"""
        from api.services.jwt_verify import verify_token
        
        result = verify_token("")
        assert result is None

    def test_verify_token_none(self):
        """None token 应返回 None"""
        from api.services.jwt_verify import verify_token
        
        result = verify_token(None)
        assert result is None

    def test_verify_demo_user(self):
        """Demo 用户 token 应返回 DEMO_USER_UUID"""
        from api.services.jwt_verify import verify_token, DEMO_USER_UUID
        
        result = verify_token("demo_user")
        assert result == DEMO_USER_UUID

    def test_verify_bearer_prefix(self):
        """Bearer 前缀应被正确处理"""
        from api.services.jwt_verify import verify_token, DEMO_USER_UUID
        
        # Demo user with Bearer prefix
        result = verify_token("Bearer demo_user")
        assert result == DEMO_USER_UUID

    @patch('api.services.jwt_verify._get_supabase_client')
    def test_verify_valid_token(self, mock_get_client):
        """有效 token 应返回用户 ID"""
        from api.services.jwt_verify import verify_token
        
        # 模拟 Supabase 客户端
        mock_supabase = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "user-uuid-123"
        mock_supabase.auth.get_user.return_value.user = mock_user
        mock_get_client.return_value = mock_supabase
        
        result = verify_token("valid.jwt.token")
        assert result == "user-uuid-123"

    @patch('api.services.jwt_verify._get_supabase_client')
    def test_verify_expired_token(self, mock_get_client):
        """过期 token 应返回 None"""
        from api.services.jwt_verify import verify_token
        
        mock_supabase = MagicMock()
        mock_supabase.auth.get_user.side_effect = Exception("Token expired")
        mock_get_client.return_value = mock_supabase
        
        result = verify_token("expired.jwt.token")
        assert result is None

    @patch('api.services.jwt_verify._get_supabase_client')
    def test_verify_invalid_token(self, mock_get_client):
        """无效 token 应返回 None"""
        from api.services.jwt_verify import verify_token
        
        mock_supabase = MagicMock()
        mock_supabase.auth.get_user.side_effect = Exception("Invalid token")
        mock_get_client.return_value = mock_supabase
        
        result = verify_token("invalid-token")
        assert result is None

    @patch('api.services.jwt_verify._get_supabase_client')
    def test_verify_token_no_user(self, mock_get_client):
        """token 验证成功但无用户信息应返回 None"""
        from api.services.jwt_verify import verify_token
        
        mock_supabase = MagicMock()
        mock_response = MagicMock()
        mock_response.user = None
        mock_supabase.auth.get_user.return_value = mock_response
        mock_get_client.return_value = mock_supabase
        
        result = verify_token("valid.jwt.token")
        assert result is None
