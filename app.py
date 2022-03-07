# Import dependencies
from flask import Flask, jsonify, escape
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from dateutil.relativedelta import relativedelta
import datetime as dt

# Create engine for connection to database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect tables
Base = automap_base()
Base.prepare(engine, reflect=True)
Measurement = Base.classes.measurement
Station = Base.classes.station

# Set up Flask
app = Flask(__name__)


# Home page
@app.route("/")
def home():
    # Format with hardcoded HTML (for now)
    return (
        "<h2>List of available routes:</h2>"
        "<p>Database calls:</p>"
        "<ul><li><a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a"
        "></li>"
        "<li><a href='/api/v1.0/stations'>/api/v1.0/stations</a></li>"
        "<li><a href='/api/v1.0/tobs'>/api/v1.0/tobs</a></li>"
        "<ul><li>Note: This only returns temperatures up to a year prior to "
        "the last recorded date from the most active station.</li></ul></ul>"
        "<p>Date calls: (returns minimum, average, and maximum temperatures "
        "from specified date)</p>"
        f"<ul><li>/api/v1.0/{escape('<start>')}</li>"
        f"<ul><li>Where {escape('<start>')} is a starting date in the ISO "
        f"8601 date format.</li></ul>"
        f"<li>/api/v1.0/{escape('<start>/<end>')}</li>"
        f"<ul><li>Where {escape('<start>/<end>')} is a starting and ending "
        f"date in the ISO 8601 date format.</li></ul></ul>"
    )


# Precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Connect
    session = Session(engine)

    # Query
    results = session.query(
        Measurement.date,
        Measurement.prcp
    ).all()

    # Close connection
    session.close()

    # Create list of dictionaries for jsonify
    all_prcp = [
        {"date": date, "prcp": prcp}
        for date, prcp in results
    ]

    # Return result
    return jsonify(all_prcp)


# Stations route
@app.route("/api/v1.0/stations")
def stations():
    # Connect
    session = Session(engine)

    # Query
    results = session.query(
        Station.station,
        Station.name,
        Station.latitude,
        Station.longitude
    ).all()

    # Close connection
    session.close()

    # Create list of dictionaries for jsonify
    all_stations = [
        {"station": station, "name": name, "latitude": lat, "longitude": long}
        for station, name, lat, long in results
    ]

    # Return result
    return jsonify(all_stations)


# TOBS route
@app.route("/api/v1.0/tobs")
def tobs():
    # Connect
    session = Session(engine)

    # Find most recent date in database
    most_recent = session.query(Measurement.date) \
        .order_by(Measurement.date.desc()).first()[0]
    end_date = dt.datetime.fromisoformat(most_recent).date()

    # Calculate year prior to date
    twelve_months_prior = end_date - relativedelta(years=1)

    # Find the most active station based on frequency of appearance
    active_stations = session.query(
        Measurement.station,
        func.count(Measurement.station)
    ).group_by(Measurement.station) \
        .order_by(func.count(Measurement.station).desc())
    most_active = active_stations[0][0]

    # Query
    results = session.query(Measurement.date, Measurement.tobs) \
        .filter(Measurement.date >= twelve_months_prior) \
        .filter(Measurement.date <= end_date).order_by(Measurement.date) \
        .filter(Measurement.station == most_active)

    # Close connection
    session.close()

    # Create list of dictionaries for jsonify
    all_tobs = [{"date": date, "tobs": temps} for date, temps in results]

    # Return result
    return jsonify(all_tobs)


# Start date route
@app.route("/api/v1.0/<start>")
def date_start_temps(start):
    # Connect
    session = Session(engine)

    try:
        # Convert user provided date to datetime
        start_date = dt.datetime.fromisoformat(start).date()
    except ValueError:
        return jsonify({"error": f"{start} is not a valid date."}), 404

    # Query
    results = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start_date)

    # Close connection
    session.close()

    # Create list of dictionaries for jsonify
    all_start_temps = [
        {"TMIN": tmin, "TAVG": tavg, "TMAX": tmax}
        for tmin, tavg, tmax in results
    ]

    # Return result
    return jsonify(all_start_temps)


@app.route("/api/v1.0/<start>/<end>")
def date_range_temps(start, end):
    # Connect
    session = Session(engine)

    try:
        # Convert user provided dates to datetime
        start_date = dt.datetime.fromisoformat(start).date()
    except ValueError:
        return jsonify({"error": f"{start} is not a valid date."}), 404
    try:
        end_date = dt.datetime.fromisoformat(end).date()
    except ValueError:
        return jsonify({"error": f"{end} is not a valid date."}), 404

    # Query
    results = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start_date)\
        .filter(Measurement.date <= end_date)

    # Close connection
    session.close()

    # Create list of dictionaries for jsonify
    all_range_temps = [
        {"TMIN": tmin, "TAVG": tavg, "TMAX": tmax}
        for tmin, tavg, tmax in results
    ]

    # Return result
    return jsonify(all_range_temps)


# For debugging
if __name__ == "__main__":
    app.run(debug=True)
