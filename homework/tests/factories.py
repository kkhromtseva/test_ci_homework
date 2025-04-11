import factory
import factory.fuzzy as fuzzy
from faker import Faker
from main.models import Client, Parking, db

fake = Faker("ru_RU")


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = db.session

    name = fake.first_name()
    surname = fake.last_name()
    credit_card = fuzzy.FuzzyChoice(choices=[fake.credit_card_number(), None])
    car_number = fake.license_plate()


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Parking
        sqlalchemy_session = db.session

    address = fake.address()
    opened = fuzzy.FuzzyChoice(choices=[True, False])
    count_places = fake.random_int(10, 50)
    count_available_places = factory.LazyAttribute(lambda obj: obj.count_places)
