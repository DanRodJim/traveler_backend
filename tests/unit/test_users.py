import pytest
from fastapi import status


@pytest.mark.unit
class TestUsers:
    """Tests de gestión de usuarios"""
    
    def test_get_my_profile(self, client, auth_headers, test_user):
        """Test obtener mi perfil"""
        response = client.get("/api/users/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
    
    def test_update_my_profile_name(self, client, auth_headers):
        """Test actualizar nombre"""
        response = client.put(
            "/api/users/me",
            headers=auth_headers,
            json={"full_name": "Updated Name"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Updated Name"
    
    def test_update_my_profile_email(self, client, auth_headers):
        """Test actualizar email"""
        response = client.put(
            "/api/users/me",
            headers=auth_headers,
            json={"email": "newemail@example.com"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newemail@example.com"
    
    def test_update_email_already_taken(self, client, auth_headers, test_user2):
        """Test actualizar a email ya en uso"""
        response = client.put(
            "/api/users/me",
            headers=auth_headers,
            json={"email": test_user2.email}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        # ✅ Cambiar de 'detail' a 'message'
        assert "error" in data
        assert data["error"] == "DuplicateResourceError"
        assert "already" in data["message"].lower() or "exist" in data["message"].lower()
    
    def test_update_password(self, client, auth_headers):
        """Test actualizar contraseña"""
        response = client.put(
            "/api/users/me",
            headers=auth_headers,
            json={"password": "newpassword123"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que puede hacer login con nueva contraseña
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": "test@example.com",
                "password": "newpassword123"
            }
        )
        assert login_response.status_code == status.HTTP_200_OK
    
    def test_get_user_by_id(self, client, auth_headers, test_user2):
        """Test obtener usuario por ID"""
        response = client.get(
            f"/api/users/{test_user2.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_user2.id)
        assert data["email"] == test_user2.email
    
    def test_get_nonexistent_user(self, client, auth_headers):
        """Test obtener usuario inexistente"""
        import uuid
        fake_id = uuid.uuid4()
        
        response = client.get(
            f"/api/users/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND