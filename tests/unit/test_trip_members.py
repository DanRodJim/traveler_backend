import pytest
from fastapi import status


@pytest.mark.unit
@pytest.mark.trips
class TestTripMembers:
    """Tests de gestión de miembros de viajes"""
    
    def test_get_trip_members(self, client, auth_headers, test_trip, test_trip_member):
        """Test obtener miembros de un viaje"""
        response = client.get(
            f"/api/trips/{test_trip.id}/members",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        member_ids = [m["user_id"] for m in data]
        assert str(test_trip_member.user_id) in member_ids
    
    def test_add_member_as_owner(self, client, auth_headers, test_trip, test_user3):
        """Test agregar miembro como owner"""
        response = client.post(
            f"/api/trips/{test_trip.id}/members",
            headers=auth_headers,
            json={
                "user_id": str(test_user3.id),
                "role": "viewer"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == str(test_user3.id)
        assert data["role"] == "viewer"
        assert data["trip_id"] == str(test_trip.id)
    
    def test_add_duplicate_member_fails(self, client, auth_headers, test_trip, test_trip_member):
        """Test agregar miembro duplicado falla"""
        response = client.post(
            f"/api/trips/{test_trip.id}/members",
            headers=auth_headers,
            json={
                "user_id": str(test_trip_member.user_id),
                "role": "editor"
            }
        )
        
        # ✅ Ahora es 400 (DuplicateResourceError)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"] == "DuplicateResourceError"
    
    def test_add_member_as_non_owner_fails(self, client, auth_headers2, test_trip, test_trip_member, test_user3):
        """Test agregar miembro como no-owner falla"""
        assert test_trip_member is not None
        
        response = client.post(
            f"/api/trips/{test_trip.id}/members",
            headers=auth_headers2,
            json={
                "user_id": str(test_user3.id),
                "role": "viewer"
            }
        )
        
        # ✅ Cambiado: 403 porque no es owner
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "error" in data
        assert data["error"] == "NotTripOwnerError"
    
    def test_update_member_role_as_owner(self, client, auth_headers, test_trip, test_trip_member):
        """Test actualizar rol de miembro como owner"""
        response = client.put(
            f"/api/trips/{test_trip.id}/members/{test_trip_member.user_id}",
            headers=auth_headers,
            json={
                "role": "viewer"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "viewer"
    
    def test_update_member_role_as_non_owner_fails(self, client, auth_headers2, test_trip, test_trip_member):
        """Test actualizar rol como no-owner falla"""
        response = client.put(
            f"/api/trips/{test_trip.id}/members/{test_trip_member.user_id}",
            headers=auth_headers2,
            json={"role": "viewer"}
        )
        
        # ✅ 403 (NotTripOwnerError)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["error"] == "NotTripOwnerError"
    
    def test_update_owner_role_fails(self, client, auth_headers, test_trip, test_user):
        """Test cambiar rol del owner falla"""
        response = client.put(
            f"/api/trips/{test_trip.id}/members/{test_user.id}",
            headers=auth_headers,
            json={
                "role": "viewer"
            }
        )
        
        # ✅ Cambiado: 403 porque no se puede cambiar rol del owner
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "error" in data
        assert data["error"] == "NotTripOwnerError"
    
    def test_remove_member_as_owner(self, client, auth_headers, test_trip, test_trip_member):
        """Test remover miembro como owner"""
        response = client.delete(
            f"/api/trips/{test_trip.id}/members/{test_trip_member.user_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que ya no es miembro
        get_response = client.get(
            f"/api/trips/{test_trip.id}/members",
            headers=auth_headers
        )
        data = get_response.json()
        member_ids = [m["user_id"] for m in data]
        assert str(test_trip_member.user_id) not in member_ids
    
    def test_remove_member_as_non_owner_fails(self, client, auth_headers2, test_trip, test_trip_member):
        """Test remover miembro como no-owner falla"""
        response = client.delete(
            f"/api/trips/{test_trip.id}/members/{test_trip_member.user_id}",
            headers=auth_headers2
        )
        
        # ✅ Cambiado: 403 porque no es owner
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "error" in data
        assert data["error"] == "NotTripOwnerError"
    
    def test_remove_nonexistent_member(self, client, auth_headers, test_trip):
        """Test remover miembro inexistente"""
        import uuid
        fake_id = uuid.uuid4()
        
        response = client.delete(
            f"/api/trips/{test_trip.id}/members/{fake_id}",
            headers=auth_headers
        )
        
        # ✅ 404 (ResourceNotFoundError)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"] == "ResourceNotFoundError"