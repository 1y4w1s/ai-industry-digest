"""
测试配置
用于在测试前设置环境变量和模拟对象
"""

import os
import pytest

# 在导入任何应用代码之前设置环境变量
@pytest.fixture(autouse=True, scope="session")
def setup_test_env():
    """设置测试环境变量"""
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
    os.environ["SUPABASE_KEY"] = "test-key"
    os.environ["DEEPSEEK_API_KEY"] = "test-api-key"
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"
    yield
