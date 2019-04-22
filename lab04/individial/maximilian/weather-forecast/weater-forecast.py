import helpers
import pyspark
import datetime
import numpy as np
from math import exp

# Data paths
tr_path = "../data/temperature-readings.csv"
sr_path = "../data/stations.csv"

# Spark content and data import
sc = pyspark.SparkContext(appName="Temperature")
sc_sql = pyspark.SparkContext(sc)

# Temperatures pre processing
temperature_readings = sc.textFile(tr_path)
# station-id, year, month, day, hour, minute, second
# [(102170, 2013, 11, 1, 6.0, 0.0, 0.0)]
temperatures = temperature_readings.map(lambda m: (int(m[0]),
                                                   int(m[1].split("-")[0]),
                                                   int(m[1].split("-")[1]),
                                                   int(m[1].split("-")[2]),
                                                   float(m[2].split(":")[0]),
                                                   float(m[2].split(":")[1]),
                                                   float(m[2].split(":")[2])))

# Stations pre processing
station_readings = sc.textFile(sr_path)
stations = station_readings.map(lambda l: l.split(";"))
# station-id, latitude, longitude
# [(102170, 60.2788, 12.8538)]
stations = stations.map(lambda m: (int(m[0]), float(m[3]), float(m[4])))
stations = sc.broadcast(value=stations)

# General parameters
h_distance = 300_000
h_date = 30
h_time = 3

# Function call parameters
latitude = 58.4166
longitude = 15.6333
date = datetime.date(2000, 5, 8)


def gaussian_kernel(vector):
    return exp(-np.square(vector))


def kernel_distance(locationA, locationB, smooting, kernel):
    raise NotImplementedError()


def kernel_day(dayA, dayB, smoothing, kernel):
    raise NotImplementedError()


def kernel_hour(hourA, hourB, smoothing, kernel):
    raise NotImplementedError()


def predict_weather(latitude, longitude, predict_date):

    # Remove all future data
    filtered_measurements = temperatures.filter(lambda m: datetime.date(m[1], m[2], m[3]) > predict_date)

    # Create the data points distributed over the day

    # Call the different kernel functions

    # Take the sum / product respectively

    return 0


predictes_temperatures = predict_weather(latitude, longitude, date)


# Close Spark context
sc.stop()
