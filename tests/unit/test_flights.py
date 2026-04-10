import pytest
from fastapi import status
from datetime import date, timedelta


@pytest.mark.unit
class TestFlights:
    """Tests de gestión de vuelos"""
    
    def test_create_flight_success(self, client, auth_headers, test_trip):
        """Test crear vuelo exitosamente"""
        departure_date = date.today() + timedelta(days=30)
        arrival_date = date.today() + timedelta(days=31)
        
        response = client.post(
            "/api/flights/",
            headers=auth_headers,
            json={
                "trip_id": str(test_trip.id),
                "airline": "United Airlines",
                "flight_number": "UA456",
                "departure_airport": "SFO",
                "arrival_airport": "NRT",
                "departure_date": departure_date.isoformat(),
                "departure_time": "15:00:00",
                "arrival_date": arrival_date.isoformat(),
                "arrival_time": "19:00:00",
                "booking_reference": "XYZ789",
                "cost": 1500.00
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["airline"] == "United Airlines"
        assert data["flight_number"] == "UA456"
        assert data["departure_airport"] == "SFO"
        assert data["arrival_airport"] == "NRT"
        assert data["cost"] == "1500.00"
    
    def test_create_flight_as_editor(self, client, auth_headers2, test_trip, test_trip_member):
        """Test crear vuelo como editor"""
        assert test_trip_member is not None
        
        departure_date = date.today() + timedelta(days=30)
        arrival_date = date.today() + timedelta(days=31)
        
        response = client.post(
            "/api/flights/",
            headers=auth_headers2,
            json={
                "trip_id": str(test_trip.id),
                "airline": "Delta",
                "flight_number": "DL999",
                "departure_airport": "LAX",
                "arrival_airport": "HND",
                "departure_date": departure_date.isoformat(),
                "departure_time": "10:00:00",
                "arrival_date": arrival_date.isoformat(),
                "arrival_time": "14:00:00"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_flight_unauthorized(self, client, auth_headers, test_trip2):
        """Test crear vuelo sin permisos"""
        departure_date = date.today() + timedelta(days=30)
        arrival_date = date.today() + timedelta(days=31)
        
        response = client.post(
            "/api/flights/",
            headers=auth_headers,
            json={
                "trip_id": str(test_trip2.id),
                "airline": "Unauthorized",
                "flight_number": "XX000",
                "departure_airport": "AAA",
                "arrival_airport": "BBB",
                "departure_date": departure_date.isoformat(),
                "arrival_date": arrival_date.isoformat()
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_flights_by_trip(self, client, auth_headers, test_trip, test_flight):
        """Test obtener vuelos de un viaje"""
        response = client.get(
            f"/api/flights/?trip_id={test_trip.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(f["id"] == str(test_flight.id) for f in data)
    
    def test_get_flight_by_id(self, client, auth_headers, test_flight):
        """Test obtener vuelo por ID"""
        response = client.get(
            f"/api/flights/{test_flight.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_flight.id)
        assert data["airline"] == test_flight.airline
        assert data["flight_number"] == test_flight.flight_number
    
    def test_get_flight_unauthorized(self, client, auth_headers, test_trip2, db):
        """Test obtener vuelo sin permisos"""
        from app.models.flight import Flight
        import uuid
        
        flight = Flight(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            airline="Private",
            flight_number="PV001",
            departure_airport="AAA",
            arrival_airport="BBB",
            departure_date=date.today(),
            arrival_date=date.today(),
            created_by=test_trip2.owner_id
        )
        db.add(flight)
        db.commit()
        
        response = client.get(
            f"/api/flights/{flight.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_flight_success(self, client, auth_headers, test_flight):
        """Test actualizar vuelo"""
        response = client.put(
            f"/api/flights/{test_flight.id}",
            headers=auth_headers,
            json={
                "airline": "Updated Airline",
                "cost": 1800.00
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["airline"] == "Updated Airline"
        assert data["cost"] == "1800.00"
    
    def test_update_flight_unauthorized(self, client, auth_headers, test_trip2, db):
        """Test actualizar vuelo sin permisos"""
        from app.models.flight import Flight
        import uuid
        
        flight = Flight(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            airline="Private",
            flight_number="PV001",
            departure_airport="AAA",
            arrival_airport="BBB",
            departure_date=date.today(),
            arrival_date=date.today(),
            created_by=test_trip2.owner_id
        )
        db.add(flight)
        db.commit()
        
        response = client.put(
            f"/api/flights/{flight.id}",
            headers=auth_headers,
            json={"airline": "Hacked"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_flight_success(self, client, auth_headers, test_flight):
        """Test eliminar vuelo"""
        response = client.delete(
            f"/api/flights/{test_flight.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que ya no existe
        get_response = client.get(
            f"/api/flights/{test_flight.id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_flight_unauthorized(self, client, auth_headers, test_trip2, db):
        """Test eliminar vuelo sin permisos"""
        from app.models.flight import Flight
        import uuid
        
        flight = Flight(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            airline="Private",
            flight_number="PV001",
            departure_airport="AAA",
            arrival_airport="BBB",
            departure_date=date.today(),
            arrival_date=date.today(),
            created_by=test_trip2.owner_id
        )
        db.add(flight)
        db.commit()
        
        response = client.delete(
            f"/api/flights/{flight.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN