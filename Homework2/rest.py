from http.server import HTTPServer, BaseHTTPRequestHandler
from sqlite3 import connect

def cursor_rows_to_json(cursor):
    result = "{ \"customers\" : ["
    for row in cursor:
        result += str(row) + ","
    result = result.replace("\'", "\"")
    result = result[:-1]
    result += '] }'
    return result

def cursor_row_to_json(cursor):
    result = str(cursor.fetchone())
    result = result.replace("\'", "\"")
    return result


class RequestsHandler(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.conn = None
        self.cursor = None


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
            self.cursor.execute("select * from customers")
            self.send_response(200)
            self.end_headers()
            result = cursor_rows_to_json(self.cursor).encode()
            self.wfile.write(result)
            return

        if "/customers/" in self.path:
            customer_id = self.path.split("/")[2]
            print("customer id: " + customer_id)
            query = "select * from customers where id=?"
            self.cursor.execute(query, (customer_id,))
            result = cursor_row_to_json(self.cursor).encode()
            if result.decode() == 'None':
                code = 404
                response = "Customer not found"
            else:
                code = 200
                response = result

            self.send_response(code)
            self.end_headers()
            self.wfile.write(response)
            return


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
        json[col[0]] = str(row[_id])
    return json


def run(server_class=HTTPServer, handler_class=RequestsHandler):
    conn = connect(r"C:\CloudComputing\Homework2\bd")
    conn.row_factory = json_factory
    handler_class.conn = conn
    handler_class.cursor = handler_class.conn.cursor()
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()