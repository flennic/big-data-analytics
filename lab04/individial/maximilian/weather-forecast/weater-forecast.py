import helpers
import pyspark
import datetime
from math import exp
from functools import partial

# Data paths
tr_path = "../data/temperature-readings-tiny.csv"
sr_path = "../data/stations.csv"

# Spark content and data import
sc = pyspark.SparkContext(appName="Temperature")

# Temperatures pre processing
temperature_readings = sc.textFile(tr_path)
# station-id, year, month, day, hour, minute, second
# [(102170, 2013, 11, 1, 6.0, 0.0, 0.0)]
temperatures = temperature_readings.map(lambda l: l.split(";"))
temperatures = temperatures.map(lambda m: (int(m[0]),
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
stations = stations.map(lambda m: (int(m[0]), (float(m[3]), float(m[4]))))

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


def min_distance(a, b, ring_size):
    if a < 0 or a > ring_size or b < 0 or b > ring_size:
        raise ValueError("Both arguments must be greater or equal to 0 and smaller or equal to ring_size.")
    return min(abs(a - b), ring_size - abs(a - b))


def kernel_distance(location, rdd_temperatures, rdd_stations, smoothing, kernel):

    distances = rdd_temperatures.map(lambda m: helpers.haversine(location[0],
                                                                        location[1],
                                                                        rdd_stations.value[m[0]][0],
                                                                        rdd_stations.value[m[0]][1]))
    #distances = rdd.map(lambda m: (m[0], helpers.haversine(location[0], location[1], m[1], m[2])))
    distances = distances.map(lambda m: kernel(m, smoothing))
    return distances


def kernel_day(day, rdd, smoothing, kernel):

    differences = rdd.map(lambda m: min_distance(datetime.date(m[1], m[2], m[3]).timetuple().tm_yday,
                                                        day.timetuple().tm_yday, 366))
    differences = differences.map(lambda m: kernel(m, smoothing))
    return differences


def kernel_hour(hour, rdd, smoothing, kernel):
    # station-id, year, month, day, hour, minute, second
    # [(102170, 2013, 11, 1, 6.0, 0.0, 0.0)]
    differences = rdd.map(lambda m: min_distance(hour.timetuple().tm_hour, m[4], 24))
    differences = differences.map(lambda m: kernel(m, smoothing))
    #differences = rdd.map(lambda m: (m[0], m[4]))
    return differences


def predict_weather(latitude, longitude, predict_date, rdd_temperatures, rdd_stations, h_distance, h_date, h_time):

    # Remove all future data and cache data
    rdd_temperatures = rdd_temperatures.filter(lambda m: datetime.date(m[1], m[2], m[3]) > predict_date).cache()
    rdd_stations = rdd_stations.collectAsMap()
    rdd_stations = sc.broadcast(value=rdd_stations)

    # Change broadcasted dataframe to rdd as we should use rdds in this lab
    #rdd_stations = rdd_stations.rdd

    # Create the data points distributed over the day
    hours = (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22)
    daytimes = tuple([datetime.datetime.combine(predict_date, datetime.time(hour, 0)) for hour in hours])

    # Call the different kernel functions

    # Distance difference
    kernel_distances = kernel_distance((latitude, longitude), rdd_temperatures, rdd_stations, h_distance, gaussian_kernel)

    # Day difference
    kernel_days = kernel_day(predict_date, rdd_temperatures, h_date, gaussian_kernel)

    # Hour difference
    kernel_hours = [kernel_hour(daytime, rdd_temperatures, h_time, gaussian_kernel) for daytime in daytimes]

    # Take the sum / product respectively
    kernel_distance_days = kernel_distances.zip(kernel_days).map(lambda m: sum(m)).cache()

    for i in range(0, len(daytimes)):
        kernel_sum = kernel_distance_days.zip(kernel_hours[i]).map(lambda m: sum(m))
        #res_sum =

    return [kernel_distances, kernel_days, kernel_hours, kernel_distance_days]


predicted_temperatures = predict_weather(latitude, longitude, date, temperatures, stations, h_distance, h_date, h_date)
res = predicted_temperatures#.take(10)
#res = map(lambda m: m[1], res)
#print(sum(map(lambda x: x[1], res)))
#res = [pred.take(10) for pred in res]
print(res[3].take(3))

# Close Spark context
sc.stop()
