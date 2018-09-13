"""
This is a very basic Flask application to demonstrate instrumenting an online
application with Prometheus.

"""

import random
import time
from uuid import uuid4

from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.exc import DataError
from sqlalchemy.orm import exc
from sqlalchemy.dialects.postgresql import UUID

from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.serving import run_simple

from prometheus_client import Counter, Gauge, Histogram, make_wsgi_app


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://prom:prom@localhost/prom'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
api = Api(app)

# use DispatcherMiddleware to route /metrics requests to prometheus_client
dispatched = DispatcherMiddleware(app, {
    '/metrics': make_wsgi_app()
})


class Widget(db.Model):
    """
    Widget is our sqlalchemy database model for a simple widget

    """
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = db.Column(db.String)
    wongles = db.Column(db.Integer)
    waggles = db.Column(db.Integer)


# prometheus instruments
WIDGET_LIST_TIME = Histogram('widget_get_seconds', 'Time spent getting a widget')
WIDGET_REQUEST_ERRORS = Counter('widget_request_errors', 'Errors processing widget requests', ['method', 'endpoint'])
WIDGET_COUNT = Gauge('widget_count', 'Number of widgets in the database')
WIDGET_COUNT.set_function(lambda: db.session.query(Widget).count())


class WidgetList(Resource):
    """
    API resource to list widgets (get) or create a new widget (post)

    """
    @WIDGET_LIST_TIME.time()
    def get(self):
        widgets = db.session.query(Widget).all()
        serialized = [
            {'id': str(widget.id), 'name': widget.name, 'wongles': widget.wongles, 'waggles': widget.waggles}
            for widget in widgets
        ]
        time.sleep(random.uniform(0.005, 10))
        return serialized

    def post(self):
        data = request.get_json()
        try:
            widget = Widget(**data)
        except TypeError:
            WIDGET_REQUEST_ERRORS.labels(method='post', endpoint='/widgets').inc(1)
            return 'invalid parameters', 400
        db.session.add(widget)
        db.session.commit()
        return 'created', 201


class WidgetDetail(Resource):
    """
    API resource to get widget details (get) or delete a widget (post)

    """
    def delete(self, widget_id):
        try:
            widget = db.session.query(Widget).filter(Widget.id == widget_id).one()
        except (DataError, exc.NoResultFound, exc.MultipleResultsFound):
            WIDGET_REQUEST_ERRORS.labels(method='delete', endpoint='/widgets/{}'.format(widget_id)).inc(1)
            return 'widget not found', 404
        db.session.delete(widget)
        db.session.commit()
        return 'deleted', 200

    def get(self, widget_id):
        widget = db.session.query(Widget).filter(Widget.id == widget_id).one()
        return {'id': str(widget.id), 'name': widget.name, 'wongles': widget.wongles, 'waggles': widget.waggles}


api.add_resource(WidgetList, '/widgets')
api.add_resource(WidgetDetail, '/widgets/<widget_id>')


if __name__ == '__main__':
    db.create_all()
    run_simple('localhost', 5000, dispatched, use_debugger=True, use_reloader=True, use_evalex=True)
