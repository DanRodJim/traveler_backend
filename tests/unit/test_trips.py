import pytest
from fastapi import status
from datetime import date, timedelta


@pytest.mark.unit
@pytest.mark.trips
class TestTrips:
    """Tests de gestión de viajes"""
    
    def test_create_trip_success(self, client, auth_headers):
        """Test crear viaje exitosamente"""
        start = date.today() + timedelta(days=30)
        end = date.today() + timedelta(days=45)
        
        response = client.post(
            "/api/trips/",
            headers=auth_headers,
            json={
                "title": "Trip to Paris",
                "destination": "Paris, France",
                "description": "Romantic getaway",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "budget": 2500.00,
                "currency": "EUR",
                "status": "planning"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Trip to Paris"
        assert data["destination"] == "Paris, France"
        assert data["budget"] == "2500.00"
        assert data["currency"] == "EUR"
        assert "id" in data
        assert "owner_id" in data
    
    def test_create_trip_invalid_dates(self, client, auth_headers):
        """Test crear viaje con fechas inválidas (end antes de start)"""
        start = date.today() + timedelta(days=45)
        end = date.today() + timedelta(days=30)
        
        response = client.post(
            "/api/trips/",
            headers=auth_headers,
            json={
                "title": "Invalid Trip",
                "destination": "Somewhere",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "currency": "USD"
            }
        )
        
        # ✅ Ahora es 400 con error handling
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert data["error"] == "InvalidDateRangeError"
        assert "date" in data["message"].lower()
    
    def test_get_all_trips_owner(self, client, auth_headers, test_trip):
        """Test obtener todos los viajes donde soy owner"""
        response = client.get("/api/trips/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(trip["id"] == str(test_trip.id) for trip in data)
    
    def test_get_all_trips_as_member(self, client, auth_headers2, test_trip, test_trip_member):
        """Test obtener viajes donde soy miembro"""
        assert test_trip_member is not None
        
        response = client.get("/api/trips/", headers=auth_headers2)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Debe incluir test_trip (donde es miembro) y test_trip2 (donde es owner)
        trip_ids = [trip["id"] for trip in data]
        assert str(test_trip.id) in trip_ids
    
    def test_get_trip_by_id_as_owner(self, client, auth_headers, test_trip):
        """Test obtener viaje por ID como owner"""
        response = client.get(
            f"/api/trips/{test_trip.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_trip.id)
        assert data["title"] == test_trip.title
    
    def test_get_trip_by_id_as_member(self, client, auth_headers2, test_trip, test_trip_member):
        """Test obtener viaje por ID como miembro"""
        assert test_trip_member is not None

        response = client.get(
            f"/api/trips/{test_trip.id}",
            headers=auth_headers2
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_trip.id)
    
    def test_get_trip_unauthorized(self, client, auth_headers, test_trip2):
        """Test obtener viaje sin permisos falla"""
        response = client.get(
            f"/api/trips/{test_trip2.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_nonexistent_trip(self, client, auth_headers):
        """Test obtener viaje inexistente"""
        import uuid
        fake_id = uuid.uuid4()
        
        response = client.get(
            f"/api/trips/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_trip_as_owner(self, client, auth_headers, test_trip):
        """Test actualizar viaje como owner"""
        response = client.put(
            f"/api/trips/{test_trip.id}",
            headers=auth_headers,
            json={
                "title": "Updated Trip Title",
                "status": "confirmed"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Trip Title"
        assert data["status"] == "confirmed"
    
    def test_update_trip_as_editor(self, client, auth_headers2, test_trip, test_trip_member):
        """Test actualizar viaje como editor"""
        assert test_trip_member is not None

        response = client.put(
            f"/api/trips/{test_trip.id}",
            headers=auth_headers2,
            json={
                "description": "Updated by editor"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Updated by editor"
    
    def test_update_trip_as_viewer_fails(self, client, db, auth_headers2, test_trip, test_trip_member):
        """Test actualizar viaje como viewer falla"""
        # Cambiar rol a viewer
        test_trip_member.role = "viewer"
        db.commit()
        
        response = client.put(
            f"/api/trips/{test_trip.id}",
            headers=auth_headers2,
            json={
                "title": "Should Fail"
            }
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_trip_unauthorized(self, client, auth_headers, test_trip2):
        """Test actualizar viaje sin permisos"""
        response = client.put(
            f"/api/trips/{test_trip2.id}",
            headers=auth_headers,
            json={
                "title": "Unauthorized Update"
            }
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_trip_as_owner(self, client, auth_headers, test_trip):
        """Test eliminar viaje como owner"""
        response = client.delete(
            f"/api/trips/{test_trip.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que ya no existe
        get_response = client.get(
            f"/api/trips/{test_trip.id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_trip_as_editor_fails(self, client, auth_headers2, test_trip, test_trip_member):
        """Test eliminar viaje como editor falla"""
        assert test_trip_member is not None

        response = client.delete(
            f"/api/trips/{test_trip.id}",
            headers=auth_headers2
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_trip_unauthorized(self, client, auth_headers, test_trip2):
        """Test eliminar viaje sin permisos"""
        response = client.delete(
            f"/api/trips/{test_trip2.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND