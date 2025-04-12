import pytest

from main.models import Client, ClientParking, Parking


@pytest.mark.parametrize("route", ["/clients", "/clients/1"])
def test_statuscode(client, route):
    response = client.get("/clients")

    assert response.status_code == 200


def test_create_client(client) -> None:
    client_data = {
        "name": "Kseniya",
        "surname": "Khromtseva",
        "credit_card": "100200",
        "car_number": "M123UG",
    }
    resp = client.post("/clients", json=client_data)

    assert resp.json["id"] == 3
    assert resp.status_code == 201


def test_create_parking(client) -> None:
    parking_data = {
        "address": "Kirov Lenina 205",
        "opened": True,
        "count_places": 100,
        "count_available_places": 100,
    }
    resp = client.post("/parkings", json=parking_data)

    assert resp.json["id"] == 2
    assert resp.status_code == 201


@pytest.mark.parking
def test_client_parking_in(client, db) -> None:
    parking = db.session.get(Parking, 1)
    parking_before = parking.count_available_places
    parking_in_data = {
        "client_id": 2,
        "parking_id": 1,
    }
    resp = client.post("/client_parkings", json=parking_in_data)
    parking_after = parking.count_available_places

    assert parking.opened == 1
    assert resp.status_code == 201
    assert parking_before > parking_after


@pytest.mark.parking
def test_client_parking_out(client, db) -> None:
    client_p = db.session.get(Client, 1)
    client_parking = db.session.get(ClientParking, 1)
    parking = db.session.get(Parking, 1)
    parking_before = parking.count_available_places
    parking_out_data = {"client_id": 1, "parking_id": 1}
    resp = client.delete("/client_parkings", json=parking_out_data)
    parking_after = parking.count_available_places

    assert resp.status_code == 200
    assert client_parking.time_in < client_parking.time_out
    assert parking_before < parking_after
    assert client_p.credit_card is not None
