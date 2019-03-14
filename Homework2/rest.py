from http.server import HTTPServer, BaseHTTPRequestHandler
from sqlite3 import connect










class RequestsHandler(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.conn = None


    def do_GET(self):
        self.handle_get()

    def do_POST(self):
        self.handle_post()

    def do_PUT(self):
        self.handle_put()

    def do_DELETE(self):
        self.handle_delete()


    def handle_get(self):


        if self.path == "/customers":
            self.send_response(200)
            self.end_headers()
            cursor = self.conn.cursor()
            cursor.execute("select * from customers")
            for row in cursor:
                self.wfile.write(str(row).encode())

            return

        if "/customers/" in self.path:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"getting customer " + self.path.split("/")[2].encode())

        if self.path == "/products":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"getting all products")
            return

        if "/products/" in self.path:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"getting product " + self.path.split("/")[2].encode())

    def handle_post(self):
        pass

    def handle_put(self):
        pass

    def handle_delete(self):
        pass


def json_factory(cursor, row):
    json = {}
    for _id, col in enumerate(cursor.description):
        json[col[0]] = row[_id]
    return json


def run(server_class=HTTPServer, handler_class=RequestsHandler):
    conn = connect(r"C:\Projects\CloudComputing\Homework2\bd")
    conn.row_factory = json_factory
    handler_class.conn = conn
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()