"""Tests for locations endpoints."""

from app.models.location import Location


class TestListLocations:
    """GET /api/v1/locations/"""

    def test_list_empty(self, client):
        response = client.get("/api/v1/locations/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_top_level_sectors(self, client, db):
        sector = Location(
            location_type="sector",
            location_name="Muhoza",
            is_active=True,
        )
        db.add(sector)
        db.commit()

        response = client.get("/api/v1/locations/")
        data = response.json()
        assert len(data) == 1
        assert data[0]["location_name"] == "Muhoza"
        assert data[0]["location_type"] == "sector"

    def test_filter_by_type(self, client, db):
        sector = Location(location_type="sector", location_name="Muhoza", is_active=True)
        db.add(sector)
        db.commit()
        db.refresh(sector)

        cell = Location(
            location_type="cell",
            location_name="Ruhengeri",
            parent_location_id=sector.location_id,
            is_active=True,
        )
        db.add(cell)
        db.commit()

        response = client.get("/api/v1/locations/?location_type=cell")
        data = response.json()
        assert len(data) == 1
        assert data[0]["location_type"] == "cell"

    def test_filter_by_parent(self, client, db):
        sector = Location(location_type="sector", location_name="Muhoza", is_active=True)
        db.add(sector)
        db.commit()
        db.refresh(sector)

        cell = Location(
            location_type="cell",
            location_name="Ruhengeri",
            parent_location_id=sector.location_id,
            is_active=True,
        )
        db.add(cell)
        db.commit()

        response = client.get(f"/api/v1/locations/?parent_location_id={sector.location_id}")
        data = response.json()
        assert len(data) == 1
        assert data[0]["location_name"] == "Ruhengeri"


class TestGetLocation:
    """GET /api/v1/locations/{id}"""

    def test_get_location_with_children(self, client, db):
        sector = Location(location_type="sector", location_name="Muhoza", is_active=True)
        db.add(sector)
        db.commit()
        db.refresh(sector)

        cell = Location(
            location_type="cell",
            location_name="Ruhengeri",
            parent_location_id=sector.location_id,
            is_active=True,
        )
        db.add(cell)
        db.commit()

        response = client.get(f"/api/v1/locations/{sector.location_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["location_name"] == "Muhoza"
        assert len(data["children"]) == 1
        assert data["children"][0]["location_name"] == "Ruhengeri"

    def test_get_nonexistent_location(self, client):
        response = client.get("/api/v1/locations/9999")
        assert response.status_code == 404
