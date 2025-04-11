from datetime import datetime, timedelta

import pytest
from main.app import create_app
from main.models import Client, ClientParking, Parking
from main.models import db as _db


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "parking: маркер для тестов 'Заезд на парковку' и 'Выезд с парковки'"
    )


@pytest.fixture
def app():
    app = create_app(test_config=True)
    app.config["TESTING"] = True
    with app.app_context():

        _db.create_all()
        client_1 = Client(
            name="Any_name",
            surname="Any_surname",
            credit_card="12345",
            car_number="F234AY",
        )
        client_2 = Client(
            name="Vitas", surname="Bref", credit_card="102030", car_number="1234"
        )
        parking = Parking(
            address="Moscow, Kremlin, Red Square",
            opened=True,
            count_places=10,
            count_available_places=9,
        )
        time_in = datetime.now()
        client_parking = ClientParking(
            client_id=1,
            parking_id=1,
            time_in=time_in,
            time_out=(time_in + timedelta(hours=9)),
        )
        _db.session.add_all([client_1, client_2, parking, client_parking])
        _db.session.commit()
        yield app
        _db.session.close()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
