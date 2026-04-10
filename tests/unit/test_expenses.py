import pytest
from fastapi import status
from datetime import date, timedelta


@pytest.mark.unit
class TestExpenses:
    """Tests de gestión de gastos"""
    
    def test_create_expense_success(self, client, auth_headers, test_trip, test_user):
        """Test crear gasto exitosamente"""
        expense_date = date.today() + timedelta(days=35)
        
        response = client.post(
            "/api/expenses/",
            headers=auth_headers,
            json={
                "trip_id": str(test_trip.id),
                "title": "Restaurant dinner",
                "amount": 120.50,
                "currency": "USD",
                "category": "food",
                "expense_date": expense_date.isoformat(),
                "paid_by": str(test_user.id),
                "split_between": [str(test_user.id)]
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Restaurant dinner"
        assert data["amount"] == "120.50"
        assert data["category"] == "food"
    
    def test_create_expense_as_editor(self, client, auth_headers2, test_trip, test_user2, test_trip_member):
        """Test crear gasto como editor"""
        assert test_trip_member is not None
        
        expense_date = date.today() + timedelta(days=35)
        
        response = client.post(
            "/api/expenses/",
            headers=auth_headers2,
            json={
                "trip_id": str(test_trip.id),
                "title": "Taxi fare",
                "amount": 25.00,
                "currency": "USD",
                "category": "transport",
                "expense_date": expense_date.isoformat(),
                "paid_by": str(test_user2.id),
                "split_between": [str(test_user2.id)]
            }
        )
        
        # ✅ Debug si falla
        if response.status_code != status.HTTP_201_CREATED:
            print(f"\n❌ Status: {response.status_code}")
            print(f"❌ Response: {response.json()}")
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_expense_unauthorized(self, client, auth_headers, test_trip2, test_user):
        """Test crear gasto sin permisos"""
        expense_date = date.today() + timedelta(days=35)
        
        response = client.post(
            "/api/expenses/",
            headers=auth_headers,
            json={
                "trip_id": str(test_trip2.id),
                "title": "Unauthorized expense",
                "amount": 50.00,
                "currency": "USD",
                "category": "other",
                "expense_date": expense_date.isoformat(),
                "paid_by": str(test_user.id),
                "split_between": [str(test_user.id)]
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_expenses_by_trip(self, client, auth_headers, test_trip, test_expense):
        """Test obtener gastos de un viaje"""
        response = client.get(
            f"/api/expenses/?trip_id={test_trip.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(e["id"] == str(test_expense.id) for e in data)
    
    def test_get_total_expenses(self, client, auth_headers, test_trip, test_expense, test_user):
        """Test obtener total de gastos"""
        # Crear gastos adicionales
        expense_date = date.today() + timedelta(days=35)
        client.post(
            "/api/expenses/",
            headers=auth_headers,
            json={
                "trip_id": str(test_trip.id),
                "title": "Shopping",
                "amount": 200.00,
                "currency": "USD",
                "category": "shopping",
                "expense_date": expense_date.isoformat(),
                "paid_by": str(test_user.id),
                "split_between": [str(test_user.id)]
            }
        )
        
        response = client.get(
            f"/api/expenses/total/{test_trip.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "trip_id" in data
        assert "total" in data
        assert float(data["total"]) >= float(test_expense.amount)
    
    def test_get_expense_by_id(self, client, auth_headers, test_expense):
        """Test obtener gasto por ID"""
        response = client.get(
            f"/api/expenses/{test_expense.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_expense.id)
        assert data["title"] == test_expense.title
    
    def test_get_expense_unauthorized(self, client, auth_headers, test_trip2, db, test_user2):
        """Test obtener gasto sin permisos"""
        from app.models.expense import Expense, ExpenseCategory
        import uuid
        
        expense = Expense(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            title="Private expense",
            amount=100.00,
            currency="USD",
            category=ExpenseCategory.other,
            expense_date=date.today(),
            paid_by=test_user2.id,
            split_between=[str(test_user2.id)]
        )
        db.add(expense)
        db.commit()
        
        response = client.get(
            f"/api/expenses/{expense.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_expense_success(self, client, auth_headers, test_expense):
        """Test actualizar gasto"""
        response = client.put(
            f"/api/expenses/{test_expense.id}",
            headers=auth_headers,
            json={
                "title": "Updated Expense",
                "amount": 100.00
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Expense"
        assert data["amount"] == "100.00"
    
    def test_update_expense_unauthorized(self, client, auth_headers, test_trip2, db, test_user2):
        """Test actualizar gasto sin permisos"""
        from app.models.expense import Expense, ExpenseCategory
        import uuid
        
        expense = Expense(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            title="Private expense",
            amount=100.00,
            currency="USD",
            category=ExpenseCategory.other,
            expense_date=date.today(),
            paid_by=test_user2.id,
            split_between=[str(test_user2.id)]
        )
        db.add(expense)
        db.commit()
        
        response = client.put(
            f"/api/expenses/{expense.id}",
            headers=auth_headers,
            json={"title": "Hacked"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_expense_success(self, client, auth_headers, test_expense):
        """Test eliminar gasto"""
        response = client.delete(
            f"/api/expenses/{test_expense.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verificar que ya no existe
        get_response = client.get(
            f"/api/expenses/{test_expense.id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_expense_unauthorized(self, client, auth_headers, test_trip2, db, test_user2):
        """Test eliminar gasto sin permisos"""
        from app.models.expense import Expense, ExpenseCategory
        import uuid
        
        expense = Expense(
            id=uuid.uuid4(),
            trip_id=test_trip2.id,
            title="Private expense",
            amount=100.00,
            currency="USD",
            category=ExpenseCategory.other,
            expense_date=date.today(),
            paid_by=test_user2.id,
            split_between=[str(test_user2.id)]
        )
        db.add(expense)
        db.commit()
        
        response = client.delete(
            f"/api/expenses/{expense.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN