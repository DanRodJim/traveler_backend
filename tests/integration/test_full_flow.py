import pytest
from fastapi import status
from datetime import date, timedelta


@pytest.mark.integration
class TestFullFlow:
    
    def test_complete_user_journey(self, client):
        # User 1 (owner)
        register_response1 = client.post(
            "/api/auth/register",
            json={
                "email": "owner@test.com",
                "password": "password123",
                "full_name": "Trip Owner"
            }
        )
        assert register_response1.status_code == status.HTTP_201_CREATED
        user1 = register_response1.json()
        
        # User 2 (member)
        register_response2 = client.post(
            "/api/auth/register",
            json={
                "email": "member@test.com",
                "password": "password123",
                "full_name": "Trip Member"
            }
        )
        assert register_response2.status_code == status.HTTP_201_CREATED
        user2 = register_response2.json()
        
        # Login
        login_response1 = client.post(
            "/api/auth/login",
            data={
                "username": "owner@test.com",
                "password": "password123"
            }
        )
        assert login_response1.status_code == status.HTTP_200_OK
        token1 = login_response1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        login_response2 = client.post(
            "/api/auth/login",
            data={
                "username": "member@test.com",
                "password": "password123"
            }
        )
        assert login_response2.status_code == status.HTTP_200_OK
        token2 = login_response2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create trip
        start = date.today() + timedelta(days=30)
        end = date.today() + timedelta(days=45)
        
        trip_response = client.post(
            "/api/trips/",
            headers=headers1,
            json={
                "title": "Amazing Japan Trip",
                "destination": "Tokyo, Kyoto, Osaka",
                "description": "2 weeks exploring Japan",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "budget": 5000.00,
                "currency": "USD",
                "status": "planning"
            }
        )
        assert trip_response.status_code == status.HTTP_201_CREATED
        trip = trip_response.json()
        trip_id = trip["id"]
        
        # Add member
        member_response = client.post(
            f"/api/trips/{trip_id}/members",
            headers=headers1,
            json={
                "user_id": user2["id"],
                "role": "editor"
            }
        )
        assert member_response.status_code == status.HTTP_201_CREATED
        
        # Create activity (as owner)
        activity_date = date.today() + timedelta(days=35)
        activity_response = client.post(
            "/api/activities/",
            headers=headers1,
            json={
                "trip_id": trip_id,
                "title": "Visit Tokyo Tower",
                "description": "Amazing view",
                "activity_date": activity_date.isoformat(),
                "start_time": "10:00:00",
                "end_time": "12:00:00",
                "location": "Tokyo Tower",
                "category": "sightseeing",
                "cost": 25.00
            }
        )
        assert activity_response.status_code == status.HTTP_201_CREATED
        activity = activity_response.json()
        
        # Create flight (as member/editor)
        flight_response = client.post(
            "/api/flights/",
            headers=headers2,
            json={
                "trip_id": trip_id,
                "airline": "JAL",
                "flight_number": "JL001",
                "departure_airport": "LAX",
                "arrival_airport": "NRT",
                "departure_date": start.isoformat(),
                "departure_time": "14:00:00",
                "arrival_date": (start + timedelta(days=1)).isoformat(),
                "arrival_time": "18:00:00",
                "cost": 1200.00
            }
        )
        assert flight_response.status_code == status.HTTP_201_CREATED
        flight = flight_response.json()
        
        # Create accommodation (as owner)
        accommodation_response = client.post(
            "/api/accommodations/",
            headers=headers1,
            json={
                "trip_id": trip_id,
                "name": "Tokyo Hilton",
                "type": "hotel",
                "address": "1-2-3 Shinjuku, Tokyo",
                "check_in_date": (start + timedelta(days=1)).isoformat(),
                "check_out_date": end.isoformat(),
                "cost": 2500.00
            }
        )
        assert accommodation_response.status_code == status.HTTP_201_CREATED
        accommodation = accommodation_response.json()
        
        # Create expense (as member/editor)
        expense_response = client.post(
            "/api/expenses/",
            headers=headers2,
            json={
                "trip_id": trip_id,
                "title": "Welcome dinner",
                "amount": 150.00,
                "currency": "USD",
                "category": "food",
                "expense_date": activity_date.isoformat(),
                "paid_by": user2["id"],
                "split_between": [user1["id"], user2["id"]]
            }
        )
        assert expense_response.status_code == status.HTTP_201_CREATED
        expense = expense_response.json()
        
        # Check if member can see everything
        trip_view = client.get(f"/api/trips/{trip_id}", headers=headers2)
        assert trip_view.status_code == status.HTTP_200_OK
        
        activities_view = client.get(f"/api/activities/?trip_id={trip_id}", headers=headers2)
        assert activities_view.status_code == status.HTTP_200_OK
        assert len(activities_view.json()) >= 1
        
        flights_view = client.get(f"/api/flights/?trip_id={trip_id}", headers=headers2)
        assert flights_view.status_code == status.HTTP_200_OK
        assert len(flights_view.json()) >= 1
        
        accommodations_view = client.get(f"/api/accommodations/?trip_id={trip_id}", headers=headers2)
        assert accommodations_view.status_code == status.HTTP_200_OK
        assert len(accommodations_view.json()) >= 1
        
        expenses_view = client.get(f"/api/expenses/?trip_id={trip_id}", headers=headers2)
        assert expenses_view.status_code == status.HTTP_200_OK
        assert len(expenses_view.json()) >= 1
        
        # Check total expenses
        total_response = client.get(f"/api/expenses/total/{trip_id}", headers=headers1)
        assert total_response.status_code == status.HTTP_200_OK
        total_data = total_response.json()
        assert float(total_data["total"]) == 150.00
        
        # Update member role
        update_role_response = client.put(
            f"/api/trips/{trip_id}/members/{user2['id']}",
            headers=headers1,
            json={"role": "viewer"}
        )
        assert update_role_response.status_code == status.HTTP_200_OK
        
        # Check that viewer cannot edit
        edit_attempt = client.put(
            f"/api/activities/{activity['id']}",
            headers=headers2,
            json={"title": "Should fail"}
        )
        assert edit_attempt.status_code == status.HTTP_403_FORBIDDEN
        
        # Update trip (as owner)
        update_trip = client.put(
            f"/api/trips/{trip_id}",
            headers=headers1,
            json={"status": "confirmed"}
        )
        assert update_trip.status_code == status.HTTP_200_OK
        
        # Delete expense
        delete_expense = client.delete(
            f"/api/expenses/{expense['id']}",
            headers=headers1
        )
        assert delete_expense.status_code == status.HTTP_204_NO_CONTENT
        
        # Check updated total expense
        total_after = client.get(f"/api/expenses/total/{trip_id}", headers=headers1)
        assert float(total_after.json()["total"]) == 0.00
        
        # Remove member
        remove_member = client.delete(
            f"/api/trips/{trip_id}/members/{user2['id']}",
            headers=headers1
        )
        assert remove_member.status_code == status.HTTP_204_NO_CONTENT
        
        # Check that ex member do not have access
        no_access = client.get(f"/api/trips/{trip_id}", headers=headers2)
        assert no_access.status_code == status.HTTP_403_FORBIDDEN
        
        # Delete trip
        delete_trip = client.delete(f"/api/trips/{trip_id}", headers=headers1)
        assert delete_trip.status_code == status.HTTP_204_NO_CONTENT
        
        print("\nFULL FLOW FINISHED SUCCESFULLY")