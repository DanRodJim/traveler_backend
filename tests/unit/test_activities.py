import pytest
from fastapi import status
from datetime import date, timedelta


@pytest.mark.unit
class TestActivities:
    """Tests de gestión de actividades"""
    
    def test_create_activity_success(self, client, auth_headers, test_trip):
        """Test crear actividad exitosamente"""
        activity_date = date.today() + timedelta(days=35)
        
        response = client.post(
            "/api/activities/",
            headers=auth_headers,
            json={
                "trip_id": str(test_trip.id),
                "title": "Visit Eiffel Tower",
                "description": "Amazing view",
                "activity_date": activity_date.isoformat(),
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "location": "Eiffel Tower",
                "category": "sightseeing",
                "cost": 25.00
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Visit Eiffel Tower"
        assert data["category"] == "sightseeing"
        assert data["cost"] == "25.00"
    
    def test_create_activity_as_editor(self, client, auth_headers2, test_trip, test_trip_member):
        """Test crear actividad como editor"""
        assert test_trip_member is not None
        
        activity_date = date.today() + timedelta(days=35)
        
        response = client.post(
            "/api/activities/",
            headers=auth_headers2,
            json={
                "trip_id": str(test_trip.id),
                "title": "Dinner reservation",
                "activity_date": activity_date.isoformat(),
                "category": "restaurant"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_activity_unauthorized(self, client, auth_headers, test_trip2):
        """Test crear actividad sin permisos"""
        activity_date = date.today() + timedelta(days=35)
        
        response = client.post(
            "/api/activities/",
            headers=auth_headers,
            json={
                "trip_id": str(test_trip2.id),
                "title": "Unauthorized Activity",
                "activity_date": activity_date.isoformat(),
                "category": "other"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_activities_by_trip(self, client, auth_headers, test_trip, test_activity):
        """Test obtener actividades de un viaje"""
        response = client.get(
            f"/api/activities/?trip_id={test_trip.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(a["id"] == str(test_activity.id) for a in data)
    
    def test_get_activities_by_date(self, client, auth_headers, test_trip, test_activity):
        """Test obtener actividades por fecha"""
        response = client.get(
            f"/api/activities/?trip_id={test_trip.id}&date={test_activity.activity_date.isoformat()}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert all(a["activity_date"] == test_activity.activity_date.isoformat() for a in data)
    
    def test_get_activity_by_id(self, client, auth_headers, test_activity):
        """Test obtener actividad por ID"""
        response = client.get(
            f"/api/activities/{test_activity.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_activity.id)
        assert data["title"] == test_activity.title
    
    def test_get_activity_unauthorized(self, client, auth_headers, test_trip2, db):
        """Test obtener actividad sin permisos"""
        from app.models.activity import Activity, ActivityCategory
        import uuid
        
        # Crear actividad en trip2
        activity = Activity(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            title="Unauthorized Activity",
            activity_date=date.today(),
            category=ActivityCategory.other,
            created_by=test_trip2.owner_id
        )
        db.add(activity)
        db.commit()
        
        response = client.get(
            f"/api/activities/{activity.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_activity_success(self, client, auth_headers, test_activity):
        """Test actualizar actividad"""
        response = client.put(
            f"/api/activities/{test_activity.id}",
            headers=auth_headers,
            json={
                "title": "Updated Activity Title",
                "cost": 30.00
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Activity Title"
        assert data["cost"] == "30.00"
    
    def test_update_activity_unauthorized(self, client, auth_headers, test_trip2, db):
        """Test actualizar actividad sin permisos"""
        from app.models.activity import Activity, ActivityCategory
        import uuid
        
        activity = Activity(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            title="Some Activity",
            activity_date=date.today(),
            category=ActivityCategory.other,
            created_by=test_trip2.owner_id
        )
        db.add(activity)
        db.commit()
        
        response = client.put(
            f"/api/activities/{activity.id}",
            headers=auth_headers,
            json={"title": "Hacked"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_activity_success(self, client, auth_headers, test_activity):
        """Test eliminar actividad"""
        response = client.delete(
            f"/api/activities/{test_activity.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que ya no existe
        get_response = client.get(
            f"/api/activities/{test_activity.id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_activity_unauthorized(self, client, auth_headers, test_trip2, db):
        """Test eliminar actividad sin permisos"""
        from app.models.activity import Activity, ActivityCategory
        import uuid
        
        activity = Activity(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            title="Some Activity",
            activity_date=date.today(),
            category=ActivityCategory.other,
            created_by=test_trip2.owner_id
        )
        db.add(activity)
        db.commit()
        
        response = client.delete(
            f"/api/activities/{activity.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN