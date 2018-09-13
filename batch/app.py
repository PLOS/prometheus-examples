"""
This is a very basic Flask application to demonstrate instrumenting an online
application with Prometheus.

"""

from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://prom:prom@localhost/prom'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
api = Api(app)


class Widget(db.Model):
    """
    Widget is our sqlalchemy database model for a simple widget

    """
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = db.Column(db.String)
    wongles = db.Column(db.Integer)
    waggles = db.Column(db.Integer)


class WidgetList(Resource):
    """
    API resource to list widgets (get) or create a new widget (post)

    """
    def get(self):
        widgets = db.session.query(Widget).all()
        serialized = [
            {'id': str(widget.id), 'name': widget.name, 'wongles': widget.wongles, 'waggles': widget.waggles}
            for widget in widgets
        ]
        return serialized

    def post(self):
        data = request.get_json()
        widget = Widget(**data)
        db.session.add(widget)
        db.session.commit()
        return 'created', 201


class WidgetDetail(Resource):
    """
    API resource to get widget details (get) or delete a widget (post)

    """
    def delete(self, widget_id):
        widget = db.session.query(Widget).filter(Widget.id == widget_id).one()
        db.session.delete(widget)
        db.session.commit()
        return 'deleted', 200

    def get(self, widget_id):
        widget = db.session.query(Widget).filter(Widget.id == widget_id).one()
        return {'id': str(widget.id), 'name': widget.name, 'wongles': widget.wongles, 'waggles': widget.waggles}


api.add_resource(WidgetList, '/')
api.add_resource(WidgetDetail, '/<widget_id>')


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
