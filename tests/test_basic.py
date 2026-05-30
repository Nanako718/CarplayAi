# 基础测试
import pytest


def test_health_check(client):
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_info(client):
    """测试API信息接口"""
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_register_and_login(client):
    """测试注册和登录"""
    # 注册
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "nickname": "测试用户",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user_id" in data

    # 登录
    response = client.post(
        "/api/v1/auth/login", json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_register_duplicate(client):
    """测试重复注册"""
    # 第一次注册
    client.post(
        "/api/v1/auth/register",
        json={"username": "duplicate", "password": "testpass123"},
    )

    # 第二次注册（应该失败）
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "duplicate", "password": "testpass123"},
    )
    assert response.status_code == 400


def test_login_wrong_password(client):
    """测试错误密码登录"""
    # 注册
    client.post(
        "/api/v1/auth/register",
        json={"username": "wrongpass", "password": "correctpass"},
    )

    # 错误密码登录
    response = client.post(
        "/api/v1/auth/login", json={"username": "wrongpass", "password": "wrongpass"}
    )
    assert response.status_code == 401
