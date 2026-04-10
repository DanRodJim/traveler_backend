import pytest
from fastapi import status
from datetime import date, timedelta


@pytest.mark.unit
class TestAccommodations:
    """Tests de gestión de alojamientos"""
    
    def test_create_accommodation_success(self, client, auth_headers, test_trip):
        """Test crear alojamiento exitosamente"""
        check_in = date.today() + timedelta(days=31)
        check_out = date.today() + timedelta(days=45)
        
        response = client.post(
            "/api/accommodations/",
            headers=auth_headers,
            json={
                "trip_id": str(test_trip.id),
                "name": "Marriott Hotel",
                "type": "hotel",
                "address": "123 Main St, Tokyo",
                "check_in_date": check_in.isoformat(),
                "check_out_date": check_out.isoformat(),
                "booking_reference": "MAR456",
                "cost": 2000.00
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Marriott Hotel"
        assert data["type"] == "hotel"
        assert data["cost"] == "2000.00"
    
    def test_create_accommodation_as_editor(self, client, auth_headers2, test_trip, test_trip_member):
        """Test crear alojamiento como editor"""
        assert test_trip_member is not None
        
        check_in = date.today() + timedelta(days=31)
        check_out = date.today() + timedelta(days=45)
        
        response = client.post(
            "/api/accommodations/",
            headers=auth_headers2,
            json={
                "trip_id": str(test_trip.id),
                "name": "Airbnb Apartment",
                "type": "apartment",
                "check_in_date": check_in.isoformat(),
                "check_out_date": check_out.isoformat()
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_accommodation_unauthorized(self, client, auth_headers, test_trip2):
        """Test crear alojamiento sin permisos"""
        check_in = date.today() + timedelta(days=31)
        check_out = date.today() + timedelta(days=45)
        
        response = client.post(
            "/api/accommodations/",
            headers=auth_headers,
            json={
                "trip_id": str(test_trip2.id),
                "name": "Unauthorized Hotel",
                "type": "hotel",
                "check_in_date": check_in.isoformat(),
                "check_out_date": check_out.isoformat()
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_accommodation_invalid_dates(self, client, auth_headers, test_trip):
        """Test crear alojamiento con check_out antes de check_in"""
        check_in = date.today() + timedelta(days=45)
        check_out = date.today() + timedelta(days=31)
        
        response = client.post(
            "/api/accommodations/",
            headers=auth_headers,
            json={
                "trip_id": str(test_trip.id),
                "name": "Invalid Hotel",
                "type": "hotel",
                "check_in_date": check_in.isoformat(),
                "check_out_date": check_out.isoformat()
            }
        )
        
        # ✅ Ahora es 400 con error handling
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert data["error"] == "InvalidDateRangeError"
        assert "date" in data["message"].lower()
    
    def test_get_accommodations_by_trip(self, client, auth_headers, test_trip, test_accommodation):
        """Test obtener alojamientos de un viaje"""
        response = client.get(
            f"/api/accommodations/?trip_id={test_trip.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(a["id"] == str(test_accommodation.id) for a in data)
    
    def test_get_accommodation_by_id(self, client, auth_headers, test_accommodation):
        """Test obtener alojamiento por ID"""
        response = client.get(
            f"/api/accommodations/{test_accommodation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_accommodation.id)
        assert data["name"] == test_accommodation.name
    
    def test_get_accommodation_unauthorized(self, client, auth_headers, test_trip2, db):
        """Test obtener alojamiento sin permisos"""
        from app.models.accommodation import Accommodation, AccommodationType
        import uuid
        
        accommodation = Accommodation(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            name="Private Hotel",
            type=AccommodationType.hotel,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=1),
            created_by=test_trip2.owner_id
        )
        db.add(accommodation)
        db.commit()
        
        response = client.get(
            f"/api/accommodations/{accommodation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_accommodation_success(self, client, auth_headers, test_accommodation):
        """Test actualizar alojamiento"""
        response = client.put(
            f"/api/accommodations/{test_accommodation.id}",
            headers=auth_headers,
            json={
                "name": "Updated Hotel Name",
                "cost": 2500.00
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Hotel Name"
        assert data["cost"] == "2500.00"
    
    def test_update_accommodation_unauthorized(self, client, auth_headers, test_trip2, db):
        """Test actualizar alojamiento sin permisos"""
        from app.models.accommodation import Accommodation, AccommodationType
        import uuid
        
        accommodation = Accommodation(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            name="Private Hotel",
            type=AccommodationType.hotel,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=1),
            created_by=test_trip2.owner_id
        )
        db.add(accommodation)
        db.commit()
        
        response = client.put(
            f"/api/accommodations/{accommodation.id}",
            headers=auth_headers,
            json={"name": "Hacked"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_accommodation_success(self, client, auth_headers, test_accommodation):
        """Test eliminar alojamiento"""
        response = client.delete(
            f"/api/accommodations/{test_accommodation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que ya no existe
        get_response = client.get(
            f"/api/accommodations/{test_accommodation.id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_accommodation_unauthorized(self, client, auth_headers, test_trip2, db):
        """Test eliminar alojamiento sin permisos"""
        from app.models.accommodation import Accommodation, AccommodationType
        import uuid
        
        accommodation = Accommodation(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            name="Private Hotel",
            type=AccommodationType.hotel,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=1),
            created_by=test_trip2.owner_id
        )
        db.add(accommodation)
        db.commit()
        
        response = client.delete(
            f"/api/accommodations/{accommodation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN