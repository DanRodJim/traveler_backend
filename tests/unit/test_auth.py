import pytest
from fastapi import status


@pytest.mark.unit
@pytest.mark.auth
class TestAuthentication:
    """Tests de autenticación (register, login)"""
    
    def test_register_user_success(self, client):
        """Test registrar nuevo usuario exitosamente"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert "id" in data
        assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registrar con email duplicado falla"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,
                "password": "password123",
                "full_name": "Duplicate User"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert data["error"] == "DuplicateResourceError"
        assert "already" in data["message"].lower() or "exist" in data["message"].lower()
    
    def test_register_invalid_email(self, client):
        """Test registrar con email inválido"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_short_password(self, client):
        """Test registrar con contraseña muy corta"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "12345",  # Menos de 6 caracteres
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_success(self, client, test_user):
        """Test login exitoso"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_login_wrong_password(self, client, test_user):
        """Test login con contraseña incorrecta"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """Test login con usuario inexistente"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_with_token(self, client, auth_headers):
        """Test obtener usuario actual con token válido"""
        response = client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
    
    def test_get_current_user_without_token(self, client):
        """Test obtener usuario sin token falla"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_invalid_token(self, client):
        """Test obtener usuario con token inválido"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED