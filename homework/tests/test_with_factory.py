from main.models import Client, Parking

from .factories import ClientFactory, ParkingFactory


def test_create_client(client, db):
    before = len(db.session.query(Client).all())
    cl = ClientFactory()
    db.session.commit()
    after = len(db.session.query(Client).all())

    assert cl.id == 3
    assert before < after


def test_create_parking(client, db):
    before = len(db.session.query(Parking).all())
    parking = ParkingFactory()
    db.session.commit()
    after = len(db.session.query(Parking).all())

    assert parking.id == 2
    assert before < after
