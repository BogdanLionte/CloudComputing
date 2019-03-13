from http.server import HTTPServer, BaseHTTPRequestHandler
from sqlite3 import connect

class Student:
    def __init__(self, IDD):
        self.IDD = IDD
        self.name = "Bogdan"

class RequestsHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        message = ""

        if self.path == "/students":
                message += "\n"


        if "/student/" in self.path:
            print("dA")
            IDD = self.path.split("/")[2]

        self.wfile.write(str(message).encode())
        return

    def do_PATCH(self):

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Patch")

    def do_POST(self):
        self.send_response(200)
        self.end_headers()

        if "/student/" in self.path:
            IDD = self.path.split("/")[2]
            student = Student(IDD)
            student.name = "nou"
        self.wfile.write(b"Post")



def run(server_class=HTTPServer, handler_class=RequestsHandler):
    conn = connect(r"C:\users\Bogdan\Desktop\bd")
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()