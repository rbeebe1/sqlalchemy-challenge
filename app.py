# Import the dependencies.
from flask import Flask, jsonify
import pandas as pd
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine, reflect=True)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Recurring Functions
#################################################

def recent_date():

    session = Session(engine)
    
    recent = session.query(measurement).order_by(measurement.date.desc()).first()

    # temp = recent.__dict__
    # recent = temp['date']

    session.close()

    return recent

def earliest_date():

    session = Session(engine)
   
    earliest = session.query(measurement).order_by(measurement.date.asc()).first()

    # temp = earliest.__dict__
    # earliest_date = temp['date']

    session.close()

    return earliest

def one_year_ago(date):
    
    date = pd.to_datetime(date)
    
    one_year_ago_date = date - dt.timedelta(days=365)
    
    return one_year_ago_date

def most_active_station():
    
    most_active = session.query(measurement.station,func.count(measurement.station))\
        .group_by(measurement.station).order_by(func.count(measurement.station).desc()).first()[0]
    
    return most_active

def summary_stats(summary,start,date):

    sum_list = []

    for min, max, avg in summary:
        summary_dict = {}
        summary_dict["Start"] = start
        summary_dict["End"] = date
        summary_dict["TAVG"] = avg
        summary_dict["TMAX"] = max
        summary_dict["TMIN"] = min
        sum_list.append(summary_dict)
    return sum_list


#################################################
# Flask Routes
#################################################

@app.route("/")
def homepage():
    # List all available routes.
    return(f"Home Page<br/>"
           f"<br/>"
           f"Available Routes:<br/>"
           f"<br/>"
           f"Route: /api/v1.0/precipitation<br/>"
           f"Description: Date and precipitation for all stations last year<br/>"
           f"<br/>"
           f"Route: /api/v1.0/stations<br/>"
           f"Description: List of all unique stations<br/>"
           f"<br/>"
           f"Route: /api/v1.0/tobs<br/>"
           f"Description: Date and Temperatures of most popular station last year<br/>"
           f"<br/>"
           f"Route: /api/v1.0/[start]<br/>"
           f"Description: Min, max, and avg temperature from start to most recent available date<br/>"
           f"Hint: Replace [start] in url with date in YYYY-MM-DD format<br/>"
           f"<br/>"
           f"Route: /api/v1.0/[start]/[end]<br/>"
           f"Description: Min, max, and avg temperature for custom date range<br/>"
           f"Hint: Replace [start] and [end] with date in YYYY-MM-DD format<br/>"
           )

@app.route("/api/v1.0/precipitation")
def precpitation():
    
    # Get the most recent date as a string
    recent_date_str = recent_date().date

    # Calculate the one-year-ago date using the string format
    one_year_ago_date = one_year_ago(recent_date_str)

    # Convert the one-year-ago date to a string representation
    one_year_ago_date_str = one_year_ago_date.strftime('%Y-%m-%d')
    
    last_year_query = session.query(measurement.date, measurement.prcp).filter(measurement.date >= one_year_ago_date_str).order_by(measurement.date).all()  

    # Convert into a dictionary
    temp_list = []
    for date,prcp in last_year_query:
        prcp_dict = {date:prcp}
        temp_list.append(prcp_dict)
    
    # Return json
    return jsonify(temp_list)

@app.route("/api/v1.0/stations")
def get_stations():
    stations = session.query(station.station).distinct()
    
    station_list = []

    for row in stations:
        station_list.append(row[0])

    return jsonify(station_list)


@app.route("/api/v1.0/tobs")
def get_tobs():
    
    # Get the most recent date as a string
    recent_date_str = recent_date().date

    # Calculate the one-year-ago date using the string format
    one_year_ago_date = one_year_ago(recent_date_str)

    # Convert the one-year-ago date to a string representation
    one_year_ago_date_str = one_year_ago_date.strftime('%Y-%m-%d')

    hist = session.query(measurement.tobs).filter(measurement.date >= one_year_ago_date_str).filter(measurement.station == most_active_station()).all()

    temp_list = []
    for x in hist:
        d = dict(x)
        temp_list.append(d)
        temp_list.append(most_active_station())

    # Return json
    return jsonify(temp_list)

@app.route("/api/v1.0/<start>")
def get_start(start):
     # Get the most recent date as a string
    recent_date_str = recent_date().date
    earliest_date_str = earliest_date().date    

    
     # Use Try to account for user errors
    
    try:

        # If the start date is out of range, return an error message
        if recent_date_str < start or earliest_date_str > start:
            return "error"
        
        # Else
        else:
            # Check that the date format is YYYY-MM-DD
            dt.datetime.strptime(start,"%Y-%m-%d")

            # Create session (link) from Python to the DB
            session = Session(engine)

            # Query for summary statistics
            summary = session.query(func.min(measurement.tobs),func.max(measurement.tobs),\
                                    func.avg(measurement.tobs)).filter(measurement.date >= start)\
                                    .filter(measurement.date <= recent_date_str)
            # Close the session
            session.close()

            # Return json
            return jsonify(summary_stats(summary,start,recent_date_str))
        
    # If there is an exception, return the error message
    except Exception as e:
        return e 
    

@app.route("/api/v1.0/<start>/<end>")
def get_start_end(start, end):
    recent_date_str = recent_date().date
    earliest_date_str = earliest_date().date  
    
    try:
        if recent_date_str < start or earliest_date_str > start\
            or recent_date_str < end or earliest_date_str > end:
            return "Error"
        else:
            dt.datetime.strptime(start,"%Y-%m-%d")
            dt.datetime.strptime(end,"%Y-%m-%d")

            session = Session(engine)

            summary_st_end = session.query(func.min(measurement.tobs),func.max(measurement.tobs),\
                                    func.avg(measurement.tobs)).filter(measurement.date >= start)\
                                    .filter(measurement.date <= end)
            
            return jsonify(summary_stats(summary_st_end,start,end))

    except:
        return 'error'


if __name__ == '__main__':
    app.run(debug=True)

session.close()

