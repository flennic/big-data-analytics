import helpers
import pyspark
import datetime
from math import exp

# Data paths
tr_path = "../data/temperature-readings-tiny.csv"
sr_path = "../data/stations.csv"

# Spark content and data import
sc = pyspark.SparkContext(appName="Temperature")

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
#stations = sc.broadcast(value=stations)

# General parameters
h_distance = 150
h_date = 30
h_time = 3

# Function call parameters
latitude = 58.4166
longitude = 15.6333
date = datetime.date(2000, 5, 8)


def gaussian_kernel(value, smoothing):
    return exp(-(value * value)) / smoothing


def kernel_distance(location, rdd, smoothing, kernel):

    # noinspection PyUnusedLocal
    distances = rdd.map(lambda m: (m[0], helpers.haversine(location[0], location[1], m[1], m[2])))
    distances = distances.map(lambda m: (m[0], kernel(m[1], smoothing)))
    return distances


def kernel_day(days, rdd, smoothing, kernel):
    raise NotImplementedError()


def kernel_hour(hours, rdd, smoothing, kernel):
    raise NotImplementedError()


def predict_weather(latitude, longitude, predict_date, rdd_temperatures, rdd_stations, h_distance, h_date, h_time):

    # Remove all future data and cache data
    filtered_measurements = rdd_temperatures.filter(lambda m: datetime.date(m[1], m[2], m[3]) > predict_date).cache()
    rdd_stations = rdd_stations.cache()

    # Change broadcasted dataframe to rdd as we should use rdds in this lab
    #rdd_stations = rdd_stations.rdd

    # Create the data points distributed over the day
    hours = (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22)
    day_times = tuple([datetime.datetime.combine(predict_date, datetime.time(hour, 0)) for hour in hours])

    # Call the different kernel functions

    # Distance difference
    kernel_distances = kernel_distance((latitude, longitude), rdd_stations, h_distance, gaussian_kernel)

    # Day difference


    # Hour difference

    # Take the sum / product respectively

    return kernel_distances


predicted_temperatures = predict_weather(latitude, longitude, date, temperatures, stations, h_distance, h_date, h_date)
res = predicted_temperatures.collect()
res = map(lambda m: m[1], res)
print(sum(res))


# Close Spark context
sc.stop()
