import datetime

import sqlalchemy
from flask import Flask, request
from sqlalchemy import and_, insert, select, update

from .models import Client, ClientParking, Parking, db


def create_app(test_config=None):
    if test_config is None:
        db_name = "sqlite:///parking.db"
    else:
        db_name = "sqlite:///test.db"
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_name
    db.init_app(app)

    @app.before_request
    def before_requests():
        db.create_all()

    @app.route("/clients", defaults={"client_id": 0}, methods=["GET", "POST"])
    @app.route("/clients/<int:client_id>")
    def clients(client_id):
        if request.method == "GET" and client_id == 0:
            result = db.session.execute(select(Client)).scalars().all()
            clients_list = []
            for client in result:
                clients_list.append(client.to_json())
            return clients_list
        elif request.method == "GET" and client_id > 0:
            result = (
                db.session.execute(select(Client).where(Client.id == client_id))
                .scalars()
                .first()
            )
            if result:
                return result.to_json()
            else:
                return {"not_found": 404}
        elif request.method == "POST" and client_id == 0:
            data = request.json

            result = db.session.execute(
                insert(Client)
                .values(
                    name=data["name"],
                    surname=data["surname"],
                    credit_card=data["credit_card"],
                    car_number=data["car_number"],
                )
                .returning(
                    Client.id,
                    Client.name,
                    Client.surname,
                    Client.credit_card,
                    Client.car_number,
                )
            ).fetchone()
            db.session.commit()
            return {
                "id": result[0],
                "name": result[1],
                "surname": result[2],
                "credit_card": result[3],
                "car_number": result[4],
            }, 201

    @app.route("/parkings", methods=["POST"])
    def add_parking_zone():
        data = request.json
        result = db.session.execute(
            insert(Parking)
            .values(
                address=data["address"],
                count_places=data["count_places"],
                count_available_places=data["count_available_places"],
            )
            .returning(
                Parking.id,
                Parking.address,
                Parking.count_places,
                Parking.count_available_places,
            )
        ).fetchone()
        db.session.commit()
        return {
            "id": result[0],
            "address": result[1],
            "count_places": result[2],
            "count_available_places": result[3],
        }, 201

    @app.route("/client_parkings", methods=["POST", "DELETE"])
    def client_parkings():
        if request.method == "POST":
            """
            если на паркинге с parking_id есть свободные места,
            водитель с client_id может заехать
            """
            data = request.json
            opened = (
                db.session.execute(
                    select(Parking.opened).where(Parking.id == data["parking_id"])
                )
                .scalars()
                .first()
            )
            if opened:
                result = db.session.execute(
                    insert(ClientParking)
                    .values(
                        client_id=data["client_id"],
                        parking_id=data["parking_id"],
                        time_in=datetime.datetime.now(),
                    )
                    .returning(ClientParking.id, ClientParking.time_in)
                ).fetchone()

                # узнает кол-во свободных мест на парковке
                count_available_places = (
                    db.session.execute(
                        select(Parking.count_available_places).where(
                            Parking.id == data["parking_id"]
                        )
                    )
                    .scalars()
                    .first()
                )

                # удаляем одно свободное парковочное место
                db.session.execute(
                    update(Parking).values(
                        count_available_places=count_available_places - 1
                    )
                )

                # снова узнаем, сколько осталось свободных мест
                count_available_places = (
                    db.session.execute(
                        select(Parking.count_available_places).where(
                            Parking.id == data["parking_id"]
                        )
                    )
                    .scalars()
                    .first()
                )

                # если на стоянке больше мест нет - меняем статус парковки на "закрыто"
                if count_available_places == 0:
                    db.session.execute(update(Parking).values(opened=False))

                db.session.commit()
                return {"id": result[0], "time_in": result[1]}, 201
            return "Все места заняты", 404

        elif request.method == "DELETE":
            """
            Выезд с парковки (количество свободных мест увеличивается, проставляем время выезда).
            В теле запроса передать client_id, parking_id. При выезде — производить оплату
            (проверьте, что у клиента привязана карта).
            """

            data = request.json
            try:
                # получаем объект клиента паркинга по их client_id и parking_id
                client_parking_obj = (
                    db.session.execute(
                        select(ClientParking).where(
                            and_(
                                ClientParking.client_id == data["client_id"],
                                ClientParking.parking_id == data["parking_id"],
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                # сохраняем в БД дату и время выезда
                client_parking_obj.time_out = datetime.datetime.now()
                time_out = client_parking_obj.time_out
            except sqlalchemy.exc.NoResultFound:
                time_out = "NoResultFound"

            # узнаем, сколько было мест на парковке до выезда
            count_available_places = (
                db.session.execute(
                    select(Parking.count_available_places).where(
                        Parking.id == data["parking_id"]
                    )
                )
                .scalars()
                .first()
            )

            # добавляем одно свободное место
            db.session.execute(
                update(Parking).values(
                    count_available_places=count_available_places + 1
                )
            )
            count_available_places = (
                db.session.execute(
                    select(Parking.count_available_places).where(
                        Parking.id == data["parking_id"]
                    )
                )
                .scalars()
                .first()
            )

            # открываем парковку, если до этого она была закрыта
            if count_available_places > 0:
                db.session.execute(update(Parking).values(opened=True))

            # проверяем, привязана ли у клиента банковская карта,
            # если карта привязана, то проводим платеж
            card = (
                db.session.execute(
                    select(Client.credit_card).where(Client.id == data["client_id"])
                )
                .scalars()
                .first()
            )
            if card:
                payment = True
            else:
                payment = False

            db.session.commit()
            return {
                "client_id": data["client_id"],
                "parking_id": data["parking_id"],
                "time_out": time_out,
                "payment": payment,
            }

    return app
