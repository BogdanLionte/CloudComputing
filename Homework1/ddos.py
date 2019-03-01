import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import requests
import json
import time
import datetime


class Metrics:
    def __init__(self, url):
        self.url = url
        self.total_time = 0
        self.average_time = 0
        self.min_time = 9999
        self.max_time = 0
        self.size = 0


def show_metrics():
    metrics = ""
    response_times = {}

    for dirpath, dirnames, filenames in os.walk("./metrics"):
        for file in filenames:
            url = file.split("_")[0]
            if url not in response_times:
                response_times[url] = Metrics(url)

            content = open(os.path.join(dirpath, file)).read()
            if content != "":
                response_time = float(open(os.path.join(dirpath, file)).read())
                response_times[url].total_time += response_time
                response_times[url].size += 1

                if response_time > response_times[url].max_time:
                    response_times[url].max_time = response_time

                if response_time < response_times[url].min_time:
                    response_times[url].min_time = response_time

        break

    for key in response_times:
        response_times[key].average_time = response_times[key].total_time / response_times[key].size
    metrics += json.dumps([item.__dict__ for item in response_times.values()])
    # metrics += "avg time for " + key + \
    #            " is " + str(response_times[key].total_time / response_times[key].size) + "\n"
    # metrics += "total time for " + key + " is " + str(response_times[key].total_time) + "\n"
    # metrics += "minimum time for " + key + " is " + str(response_times[key].min_time) + "\n"
    # metrics += "maximum time for " + key + " is " + str(response_times[key].max_time) + "\n"
    # metrics += "number of requests " + key + " is " + str(response_times[key].size) + "\n"
    # metrics += "\n"

    return metrics


def generate_metrics():
    config = json.load(open("config.json"))
    ddos(config["nrBatches"], config["batchSize"],
         "https://api.random.org/json-rpc/2/invoke", "POST", get_first_request_body())
    ddos(config["nrBatches"], config["batchSize"], "http://www.splashbase.co/api/v1/images/", "GET", "3")
    request_body = {'apikey': config["virusAPIKey"],
                    'url': "3"}
    ddos(config["nrBatches"], config["batchSize"], "https://www.virustotal.com/vtapi/v2/url/scan", "POST", request_body)


def log_request(url, data, response, latency):
    config = json.load(open("config.json"))
    f = open(config["requestsLogFile"], "a+")
    f.write(datetime.datetime.now().isoformat() + "\nURL:" + url + "\nParameters: " + str(data) +
            "\nResponse:" + response + "\nLatency: " + latency + "\n\n")


def get_request_logs():
    config = json.load(open("config.json"))
    if not os.path.isfile(config["requestsLogFile"]):
        f = open(config["requestsLogFile"], "w+")
        f.close()
    f = open(config["requestsLogFile"], "r+")
    return f.read()


class RequestsHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()

        message = "Nothing here"

        if self.path == "/generateMetrics":
            generate_metrics()
            message = "<a href=\"http://localhost:8000/showMetrics\">Metrics</a>"

        if self.path == "/showMetrics":
            message = show_metrics()

        if self.path == "/getResult":
            message = get_result()

        if self.path == "/getRequestLogs":
            message = get_request_logs()

        self.wfile.write(bytes(message, "utf8"))
        return


def run(server_class=HTTPServer, handler_class=RequestsHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


def thread_handler(batch, req, url, request_type, data):
    url_name = url.split("/")[2]  # get location

    # create dir if not exists
    if not os.path.exists("./metrics"):
        os.mkdir("metrics")

    file = open(
        "./metrics/" + url_name + "_" + str(batch) + str(req) + datetime.datetime.now().isoformat().replace(":", "-"),
        "w+")
    start = time.time()
    send_request(url, request_type, data)
    end = time.time()

    file.write(str(end - start))


def ddos(nr_batches, batch_size, url, request_type, data):
    for batch in range(0, int(nr_batches)):
        for req in range(0, int(batch_size)):
            thread = Thread(target=thread_handler, args=(batch, req, url, request_type, data))
            thread.start()

        time.sleep(3)


def send_request(url, request_type, data):
    result = {}
    if request_type == "GET":
        result = requests.get(url)

    if request_type == "POST":
        result = requests.post(url, json=data)

    if request_type == "PUT":
        result = requests.put(url, json=data)

    if request_type == "DELETE":
        result = requests.delete(url, json=data)

    if request_type == "HEAD":
        result = requests.head(url, json=data)

    if request_type == "PATCH":
        result = requests.patch(url, json=data)

    return result


def get_first_request_body():
    config = json.load(open("config.json"))
    data = {'jsonrpc': "2.0", 'method': "generateIntegers"}
    params = {'apiKey': config["randomAPIKey"], 'n': 1, 'min': 1, 'max': 100}
    data['params'] = params
    data['id'] = 42

    return data


def send_first_request():
    data = get_first_request_body()

    start = time.time()
    response = send_request("https://api.random.org/json-rpc/2/invoke", "POST", data)
    end = time.time()
    log_request("https://api.random.org/json-rpc/2/invoke", data, response.text, str(end-start))
    response = json.loads(response.text)

    return response["result"]["random"]["data"][0]


def send_second_request(param):
    url = "http://www.splashbase.co/api/v1/images/" + str(param)
    start = time.time()
    response = send_request(url, "GET", None)
    end = time.time()
    log_request("http://www.splashbase.co/api/v1/images/", param, response.text, str(end-start))


    response = json.loads(response.text)
    return response["url"]


def send_third_request(param):
    config = json.load(open("config.json"))
    params = {'apikey': config["virusAPIKey"],
              'url': param}
    start = time.time()
    response = requests.post('https://www.virustotal.com/vtapi/v2/url/scan', data=params)
    end = time.time()
    log_request("https://www.virustotal.com/vtapi/v2/url/scan", param, response.text, str(end-start))
    response = json.loads(response.text)

    return str(response)


def get_result():
    first_request_result = send_first_request()

    second_request_result = send_second_request(first_request_result)

    third_request_result = send_third_request(second_request_result)

    return third_request_result


run()
