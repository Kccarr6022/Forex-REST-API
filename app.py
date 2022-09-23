from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_lambda import FlaskLambda
from tradingview_ta import TA_Handler, Interval, Exchange
from datetime import datetime
import threading
import time
import os

closing_times = [
    "21:00:00",
    "17:00:00",
    "13:00:00",
    "9:00:00",
    "5:00:00",
    "1:00:00"]

# init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))  # base directory
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)


# db class
class POST(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String(100))
    close = db.Column(db.Float)

    def __init__(self, id, time, close):
        self.id = id
        self.time = time
        self.close = close


# Schema
class PostSchema(ma.Schema):
    class Meta:
        fields = ('close', 'time')


# Init schema
post_schema = PostSchema()
posts_schema = PostSchema(many=True)

# init data stream from trading view
usdcad = TA_Handler(
    symbol="USDCAD",
    screener="forex",
    exchange="FX_IDC",
    interval=Interval.INTERVAL_4_HOURS,
)


def collect_closes():
    """Function that collects and stores all 4 hour closes in database
    """

    while True:
        if datetime.now().strftime("%H:%M:%S") in closing_times:
            rownum = db.session.query(POST).count()
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            closeprice = usdcad. get_analysis(
            ).indicators["close"]  # close at 4hr
            candle = POST(id=rownum, time=current_time, close=closeprice)
            db.session.add(candle)
            db.session.commit()
            time.sleep(14000)


@app.route('/', methods=['GET'])
def currentclose():
    candle = db.session.query(POST).order_by(POST.id.desc()).first()
    return post_schema.jsonify(candle)


@app.route('/closes', methods=['GET'])
def fourhourclose():
    data = db.session.query(POST).all()
    return posts_schema.jsonify(data)


def main():
    threading.Thread(target=collect_closes).start()
    threading.Thread(target=app.run(host='0.0.0.0', port=8080,
                     debug=True, threaded=True)).start()


# run api endpoint
if __name__ == '__main__':
    main()
