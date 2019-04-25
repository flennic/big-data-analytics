import helpers
import pyspark
import datetime
from math import exp


# Data paths
tr_path = "../../../../data/temperature-readings.csv"
sr_path = "../../../../data/stations.csv"

# Spark content and data import
sc = pyspark.SparkContext(appName="Temperature")

# Temperatures pre processing
temperature_readings = sc.textFile(tr_path)
# station-id, year, month, day, hour, minute, second, temperature
# [(102170, 2013, 11, 1, 6.0, 0.0, 0.0, 6.0)]
temperatures = temperature_readings.map(lambda l: l.split(";"))
temperatures = temperatures.map(lambda m: (int(m[0]),
                                           int(m[1].split("-")[0]),
                                           int(m[1].split("-")[1]),
                                           int(m[1].split("-")[2]),
                                           float(m[2].split(":")[0]),
                                           float(m[2].split(":")[1]),
                                           float(m[2].split(":")[2]),
                                           float(m[3])))

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
latitude = 60.2788
longitude = 12.8538
date = datetime.date(2013, 11, 1)


def gaussian_kernel(value, smoothing):
    """
    Implementation of the gaussian kernel.
    :param value: The value for which the kernel should be applied.
    :param smoothing: The smoothing factor h to apply.
    :return: The gaussian kernel applied to the given value.
    """
    return exp(-(value * value)) / smoothing


def min_distance(a, b, ring_size):
    """
    Calculates the shortest distance on a ring between two points.
    :param a: Point a.
    :param b: Point b.
    :param ring_size: Size of the ring
    :return: The shortest difference between a and b on the given 1-dimensional ring.
    """
    if a < 0 or a > ring_size or b < 0 or b > ring_size:
        raise ValueError("Both arguments must be greater or equal to 0 and smaller or equal to ring_size.")
    return min(abs(a - b), ring_size - abs(a - b))


def kernel_distance(location, rdd_temperatures, rdd_stations, smoothing, kernel):
    """
    Calculates all distances from the location to the locations in the supplied RDD.
    :param location: The given location.
    :param rdd_temperatures: An RDD with the first entry being the latitude and the second entry the longitude.
    :param rdd_stations: An RDD where the first entry is a tuple or list containing latitude and longitude.
    :param smoothing: Smoothing factor for the supplied kernel.
    :param kernel: A kernel function.
    :return: Returns all distances from location to all locations found in rdd_temperatures.
    """
    distances = rdd_temperatures.map(lambda m: helpers.haversine(location[0],
                                                                 location[1],
                                                                 rdd_stations.value[m[0]][0],
                                                                 rdd_stations.value[m[0]][1]))
    distances = distances.map(lambda m: kernel(m, smoothing))
    return distances


def kernel_day(day, rdd, smoothing, kernel):
    """
    Calculates all distances from the given day to all dates in the supplied RDD.
    :param day: A datetime object specifying the day of the year.
    :param rdd: An RDD where m[1:3] contain year, month and day.
    :param smoothing: Smoothing factor for the supplied kernel.
    :param kernel: A kernel function.
    :return: Returns all distances from day to all days found in RDD.
    """
    differences = rdd.map(lambda m: min_distance(datetime.date(m[1], m[2], m[3]).timetuple().tm_yday,
                                                 day.timetuple().tm_yday, 366))
    differences = differences.map(lambda m: kernel(m, smoothing))
    return differences


def kernel_hour(hour, rdd, smoothing, kernel):
    """
    Calculates all distances from the given hour to all hours in the supplied RDD.
    :param hour: A datetime object specifying the hour of the day.
    :param rdd: An RDD where m[4] is the hour of the day.
    :param smoothing: Smoothing factor for the supplied kernel.
    :param kernel: A kernel function.
    :return: Returns all distances from hour to all hours found in RDD.
    """
    differences = rdd.map(lambda m: min_distance(hour.timetuple().tm_hour, m[4], 24))
    differences = differences.map(lambda m: kernel(m, smoothing))
    return differences


def predict_weather(latitude,
                    longitude,
                    predict_date,
                    rdd_temperatures,
                    rdd_stations,
                    h_distance,
                    h_date,
                    h_time,
                    kernel,
                    include_product=False):
    """
    Predicts the weather for the given day.
    :param latitude: Latitude of the desired location.
    :param longitude: Longitude of the desired location.
    :param predict_date: The date where to predict the weather.
    :param rdd_temperatures: An RDD containing temperature information. Check documentation on course page.
    :param rdd_stations: An RDD containing station information. Check documentation on course page.
    :param h_distance: Smoothing factor for the distance.
    :param h_date: Smoothing factor for the date.
    :param h_time: Smoothing factor for the time.
    :param kernel: A kernel function.
    :param include_product: Specifies if the product of the kernels should also be calculated. Default is 'False'.
    :return: Returns a list with the predicted temperature for all even hours of the given date.
    """
    # Remove all future data and cache data
    rdd_temperatures = rdd_temperatures.filter(lambda m: datetime.date(m[1], m[2], m[3]) > predict_date).cache()
    # Collect as a dictionary
    rdd_stations = rdd_stations.collectAsMap()
    # Broadcast to make available
    rdd_stations = sc.broadcast(value=rdd_stations)

    # Create the data points distributed over the day
    hours = (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22)
    daytimes = tuple([datetime.datetime.combine(predict_date, datetime.time(hour, 0)) for hour in hours])

    # Call the different kernel functions

    # Distance difference
    kernel_distances = kernel_distance((latitude, longitude), rdd_temperatures, rdd_stations, h_distance,
                                       kernel)

    # Day difference
    kernel_days = kernel_day(predict_date, rdd_temperatures, h_date, kernel)

    # Hour difference
    kernel_hours = [kernel_hour(daytime, rdd_temperatures, h_time, kernel) for daytime in daytimes]

    # Combine fixed kernels
    kernel_distance_days_sum = kernel_distances.zip(kernel_days).map(lambda m: sum(m)).cache()

    if include_product:
        kernel_distance_days_prod = kernel_distances.zip(kernel_days).map(lambda m: helpers.prod(m)).cache()

    # For storing the predictions
    temperature_predictions = [None] * len(daytimes)

    for i in range(0, len(daytimes)):

        # Add the non fixed kernel (moving over day)
        kernel_sum = kernel_distance_days_sum.zip(kernel_hours[i]).map(lambda m: sum(m))

        # Include the temperatures for calculations
        res_sum = kernel_sum.zip(rdd_temperatures).map(lambda m: (m[0], m[1][7]))

        # Apply the formulas from slides
        res_sum = res_sum.map(lambda m: (m[0] * m[1], m[0]))
        res_sum = res_sum.reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]))

        if include_product:

            # Add the non fixed kernel (moving over day)
            kernel_prod = kernel_distance_days_prod.zip(kernel_hours[i]).map(lambda m: helpers.prod(m))

            # Include the temperatures for calculations
            res_prod = kernel_prod.zip(rdd_temperatures).map(lambda m: (m[0], m[1][7]))

            # Apply the formulas from slides
            res_prod = res_prod.map(lambda m: (m[0] * m[1], m[0]))
            res_prod = res_prod.reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]))

        # Store the result
        result = [res_sum[0] / res_sum[1]]

        if include_product:
            result.append(res_prod[0] / res_prod[1])

        temperature_predictions[i] = result

    return temperature_predictions


predicted_temperatures = predict_weather(latitude, longitude, date, temperatures, stations,
                                         h_distance, h_date, h_date, gaussian_kernel, True)
res = predicted_temperatures  # .take(10)

print(res)

# Close Spark context
sc.stop()
