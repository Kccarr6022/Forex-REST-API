from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from tradingview_ta import TA_Handler, Interval, Exchange
from datetime import datetime
import threading
import time
import os

times = ["20:59:59", "16:59:59", "12:59:59", "8:59:59", "4:59:59", "0:59:59"]

#init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__)) #base directory
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

# Data from tables
class POST(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    time = db.Column(db.String(100), unique=True)
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

    while True:
        if datetime.now() in times:
            rownum = db.session.query(POST).count()
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            closeprice = usdcad. get_analysis().indicators["close"] # close at 4hr
            candle = POST(id = rownum, time = current_time, close= closeprice)
            db.session.add(candle)
            db.session.commit()
            time.sleep(14000)

@app.route('/', methods=['GET'])
def currentclose():
    rownum = db.session.query(POST).count()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    closeprice = usdcad. get_analysis().indicators["close"] # close at 4hr
    candle = POST(id = rownum, time = current_time, close= closeprice)
    db.session.add(candle)
    db.session.commit()

    return post_schema.jsonify(candle)

@app.route('/USDCAD4hr', methods=['GET'])
def fourhourclose():
    rownum = db.session.query(POST).count()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    closeprice = usdcad. get_analysis().indicators["close"] # close at 4hr
    candle = POST(id = rownum, time = current_time, close= closeprice)
    db.session.add(candle)
    db.session.commit()

    return post_schema.jsonify(candle)

def main():
    threading.Thread(target=collect_closes).start()
    threading.Thread(target=app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)).start()
#run api endpoint
if __name__ == '__main__':
    main()