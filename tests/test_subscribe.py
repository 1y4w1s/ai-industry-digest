"""订阅端点测试（网站优化：自助订阅简报）

覆盖：全新邮箱订阅 / 已订阅幂等 / 退订后重新激活 / 邮箱格式校验。
DB 通过 patch api.routes.newsletter.get_db 模拟，不触真实 Supabase。
"""
import sys
sys.path.insert(0, 'tests')

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient


def _make_client():
    with patch('api.models.database.create_client'), \
         patch('api.models.database.DatabaseManager._create_client'):
        from api.main import app
        return TestClient(app)


def _fake_db(existing_rows):
    """构造一个 fake DatabaseManager：select 返回 existing_rows，insert/update 均成功"""
    db = MagicMock()
    sel = MagicMock()
    sel.data = existing_rows
    sel.execute.return_value = sel
    sel.eq.return_value = sel
    db.client.table.return_value.select.return_value = sel
    db.client.table.return_value.insert.return_value = MagicMock(
        execute=MagicMock(return_value=MagicMock(data=[{'id': 1}]))
    )
    upd = MagicMock()
    upd.eq.return_value = MagicMock(execute=MagicMock(return_value=MagicMock(data=[{'ok': True}])))
    db.client.table.return_value.update.return_value = upd
    return db


def test_subscribe_new_email():
    client = _make_client()
    db = _fake_db([])
    with patch('api.routes.newsletter.get_db', return_value=db):
        resp = client.post('/subscribe', json={'email': 'new@example.com'})
    assert resp.status_code == 200
    body = resp.json()
    assert body['ok'] is True
    assert body['status'] == 'subscribed'
    db.client.table.assert_called_with('newsletter_subscribers')


def test_subscribe_already_active():
    client = _make_client()
    db = _fake_db([{'id': 1, 'status': 'active', 'token': 't'}])
    with patch('api.routes.newsletter.get_db', return_value=db):
        resp = client.post('/subscribe', json={'email': 'old@example.com'})
    assert resp.status_code == 200
    assert resp.json()['status'] == 'already'


def test_subscribe_reactivate():
    client = _make_client()
    db = _fake_db([{'id': 1, 'status': 'unsubscribed', 'token': 't'}])
    with patch('api.routes.newsletter.get_db', return_value=db):
        resp = client.post('/subscribe', json={'email': 'back@example.com'})
    assert resp.status_code == 200
    assert resp.json()['status'] == 'reactivated'


def test_subscribe_invalid_email():
    client = _make_client()
    with patch('api.routes.newsletter.get_db') as g:
        g.return_value = _fake_db([])
        resp = client.post('/subscribe', json={'email': 'not-an-email'})
    assert resp.status_code == 400
    assert '邮箱' in resp.json()['detail']
