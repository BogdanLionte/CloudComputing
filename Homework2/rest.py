from http.server import HTTPServer, BaseHTTPRequestHandler
from sqlite3 import connect
import json
def cursor_rows_to_json(cursor, table_name):
    result = "{ \"" + table_name + "\" : ["
    for row in cursor:
        result += str(row) + ","
    result = result.replace("\'", "\"")
    result = result[:-1]
    result += '] }'
    return result

valid_routes = ["customers", "products", "orders"]

def cursor_row_to_json(cursor):
    result = str(cursor.fetchone())
    result = result.replace("\'", "\"")
    return result

def exists(cursor, table_name, id):
    query = "select * from " + table_name + " where id=?"
    cursor.execute(query, (id,))
    result = cursor_row_to_json(cursor).encode()
    if result.decode() == 'None':
        return False
    return True

def is_request_body_valid(body, path):
    if "/customers" in path:
        if "name" in body.keys() \
                and "address" in body.keys() and "phone_number" in body.keys():
            return True
    if "/products" in path:
        if "name" in body.keys() and "price" in body.keys():
            return True
    if "/orders" in path:
        if "customer_id" in body.keys() and "product_id" in body.keys():
            return True

    return False

def is_request_body_valid_for_put(body, path):
    if "/customers" in path:
        if "id" in body.keys() or "name" in body.keys() \
                or "address" in body.keys() or "phone_number" in body.keys():
            return True
    if  "/products/" in path:
        if "id" in body.keys() \
                or "name" in body.keys() or "price" in body.keys():
            return True
    if  "/orders" in path:
        if "id" in body.keys() or "customer_id" in body.keys() \
                or "product_id" in body.keys():
            return True
    return False

class RequestsHandler(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.conn = None
        self.cursor = None


    def do_GET(self):
        if self.path.split("/")[1] not in valid_routes:
            self.send_response(404)
            self.end_headers()
            return
        self.handle_get()

    def do_POST(self):
        if self.path.split("/")[1] not in valid_routes:
            self.send_response(404)
            self.end_headers()
            return
        self.handle_post()

    def do_PUT(self):
        if self.path.split("/")[1] not in valid_routes:
            self.send_response(404)
            self.end_headers()
            return
        self.handle_put()

    def do_DELETE(self):
        if self.path.split("/")[1] not in valid_routes:
            self.send_response(404)
            self.end_headers()
            return
        self.handle_delete()

    def handle_get(self):

        if "/customers/" in self.path and "/products" in self.path:
            customer_id = self.path.split("/")[2]
            query = "select product_id from orders where customer_id=?"
            self.cursor.execute(query, (customer_id,))
            product_ids = []
            for row in self.cursor.fetchall():
                product_ids.append(row["product_id"])

            response = "["
            for product_id in product_ids:
                query = "select name from products where id=?"
                self.cursor.execute(query, (product_id,))
                product_name = self.cursor.fetchone()
                response += str(product_name) + ", "
            response = response[:-2]
            response += "]"
            response = response.replace("\'", "\"")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(response.encode())

            return

        if self.path == "/customers":
            self.cursor.execute("select * from customers")
            self.send_response(200)
            self.end_headers()
            result = cursor_rows_to_json(self.cursor, "customers").encode()
            self.wfile.write(result)
            return

        if "/customers/" in self.path:
            customer_id = self.path.split("/")[2]
            query = "select * from customers where id=?"
            self.cursor.execute(query, (customer_id,))
            result = cursor_row_to_json(self.cursor).encode()
            if result.decode() == 'None':
                code = 404
                response = "Customer {0} not found".format(customer_id).encode()
            else:
                code = 200
                response = result

            self.send_response(code)
            self.end_headers()
            self.wfile.write(response)
            return


        if self.path == "/products":
            self.cursor.execute("select * from products")
            self.send_response(200)
            self.end_headers()
            result = cursor_rows_to_json(self.cursor, "products").encode()
            self.wfile.write(result)
            return

        if "/products/" in self.path:
            product_id = self.path.split("/")[2]
            query = "select * from products where id=?"
            self.cursor.execute(query, (product_id,))
            result = cursor_row_to_json(self.cursor).encode()
            if result.decode() == 'None':
                code = 404
                response = "Product {0} not found".format(product_id).encode()
            else:
                code = 200
                response = result

            self.send_response(code)
            self.end_headers()
            self.wfile.write(response)
            return

    def handle_post(self):
        content_len = int(self.headers.get('Content-Length'))
        string_post_body = self.rfile.read(content_len).decode()
        try:
            json_body = json.loads(string_post_body)
        except ValueError as e:
            self.send_response(415)
            self.end_headers()
            self.wfile.write("Invalid json".encode())
            return

        if "/products" == self.path:
            query = "select max(id) from products"
            self.cursor.execute(query)
            product_id = int(self.cursor.fetchone()["max(id)"])
            product_id += 1

            if not is_request_body_valid(json_body, self.path):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid json")
                return
            if exists(self.cursor, "products", product_id):
                self.send_response(409)
                self.end_headers()
                self.wfile.write("Product with id {0} already exists".format(product_id).encode())
                return
            query = "insert into products values (?, ?, ?)"
            self.cursor.execute(query, (product_id, json_body["name"], json_body["price"]))
            self.conn.commit()
            self.send_response(201)
            self.end_headers()
            self.wfile.write("http://localhost:8000/products/{0}".format(product_id).encode())


        if "/customers" == self.path:
            query = "select max(id) from customers"
            self.cursor.execute(query)
            customer_id = int(self.cursor.fetchone()["max(id)"])
            customer_id += 1
            if not is_request_body_valid(json_body, self.path):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid json")
                return
            if exists(self.cursor, "customers", customer_id):
                self.send_response(409)
                self.end_headers()
                self.wfile.write("Customer with id {0} already exists".format(customer_id).encode())
                return

            query = "insert into customers values (?, ?, ?, ?)"
            self.cursor.execute(query, (customer_id, json_body["name"],
                                        json_body["address"], json_body["phone_number"]))
            self.conn.commit()
            self.send_response(201)
            self.end_headers()
            self.wfile.write("http://localhost:8000/customers/{0}".format(customer_id).encode())


        if "/orders" == self.path:
            query = "select max(id) from orders"
            self.cursor.execute(query)
            order_id = int(self.cursor.fetchone()["max(id)"])
            order_id += 1
            if not is_request_body_valid(json_body, self.path):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid json")
                return
            if exists(self.cursor, "orders", order_id):
                self.send_response(409)
                self.end_headers()
                self.wfile.write("Order with id {0} already exists".format(order_id).encode())
                return

            query = "insert into products values (?, ?, ?)"
            self.cursor.execute(query, (order_id, json_body["customer_id"], json_body["product_id"]))
            self.conn.commit()
            self.send_response(201)
            self.end_headers()
            self.wfile.write("http://localhost:8000/orders/{0}".format(order_id).encode())



        if "/products/" in self.path:
            product_id = self.path.split("/")[2]
            if not is_request_body_valid(json_body, self.path):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid json")
                return
            if exists(self.cursor, "products", product_id):
                self.send_response(409)
                self.end_headers()
                self.wfile.write("Product with id {0} already exists".format(product_id).encode())
                return
            query = "insert into products values (?, ?, ?)"
            self.cursor.execute(query, (product_id, json_body["name"], json_body["price"]))
            self.conn.commit()
            self.send_response(201)
            self.end_headers()
            self.wfile.write("Added new product with id {0}, {1}".format(product_id, json_body).encode())

        if "/customers/" in self.path:
            customer_id = self.path.split("/")[2]
            if not is_request_body_valid(json_body, self.path):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid json")
                return
            if exists(self.cursor, "customers", customer_id):
                self.send_response(409)
                self.end_headers()
                self.wfile.write("Customer with id {0} already exists".format(customer_id).encode())
                return
            query = "insert into customers values (?, ?, ?, ?)"
            self.cursor.execute(query, (customer_id, json_body["name"], json_body["address"],
                                        json_body["phone_number"]))
            self.conn.commit()
            self.send_response(201)
            self.end_headers()
            self.wfile.write("Added new customer with id {0}, {1}".format(customer_id, json_body).encode())


        if "/orders/" in self.path:
            order_id = self.path.split("/")[2]
            if not is_request_body_valid(json_body, self.path):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid json")
                return
            if exists(self.cursor, "orders", order_id):
                self.send_response(409)
                self.end_headers()
                self.wfile.write("Order with id {0} already exists".format(order_id).encode())
                return
            query = "insert into orders values (?, ?, ?, ?)"
            self.cursor.execute(query, (order_id, json_body["customer_id"], json_body["product_id"]))
            self.conn.commit()
            self.send_response(201)
            self.end_headers()
            self.wfile.write("Added new order with id {0}, {1}".format(order_id, json_body).encode())


    def handle_put(self):
        content_len = int(self.headers.get('Content-Length'))
        string_post_body = self.rfile.read(content_len).decode()
        try:
            json_body = json.loads(string_post_body)
        except ValueError as e:
            self.send_response(415)
            self.end_headers()
            self.wfile.write("Invalid json".encode())
            return

        if "/products/" in self.path:
            products_id = self.path.split("/")[2]
            if not is_request_body_valid_for_put(json_body, self.path):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid json")
                return
            if exists(self.cursor, "products", products_id):
                query = "update products set "
                for key in json_body.keys():
                    query += key + " = ?, "
                query = query[:-2]
                query += " where id = \'" + products_id + "\'"
                self.cursor.execute(query, tuple(json_body.values()))
                self.conn.commit()
                self.send_response(200)
                self.end_headers()
                self.wfile.write("Updated product with id {0}".format(products_id).encode())
                return
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write("Product with id {0} does not exist".format(products_id).encode())

        if "/customers/" in self.path:
            customer_id = self.path.split("/")[2]
            if not is_request_body_valid_for_put(json_body, self.path):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid json")
                return
            if exists(self.cursor, "customers", customer_id):
                query = "update customers set "
                for key in json_body.keys():
                    query += key + " = ?, "
                query = query[:-2]
                query += " where id = \'" + customer_id + "\'"
                self.cursor.execute(query, tuple(json_body.values()))
                self.conn.commit()
                self.send_response(200)
                self.end_headers()
                self.wfile.write("Updated customer with id {0}".format(customer_id).encode())
                return
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write("Product with id {0} does not exist".format(customer_id).encode())

        if "/orders/" in self.path:
            order_id = self.path.split("/")[2]
            if not is_request_body_valid(json_body, self.path):
                self.send_response(400)
                self.end_headers()
                return
            if exists(self.cursor, "orders", order_id):
                query = "update products set "
                for key in json_body.keys():
                    query += key + " = ?, "
                query = query[:-2]
                query += " where id = \'" + order_id + "\'"
                self.cursor.execute(query, tuple(json_body.values()))
                self.conn.commit()
                self.send_response(200)
                self.end_headers()
                self.wfile.write("Updated product with id {0}".format(order_id).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write("Product with id {0} does not exist".format(order_id).encode())

        if self.path in ["/orders", "/products", "/customers"]:
            self.send_response(405)
            self.end_headers()
            self.wfile.write("Not allowed".encode())

    def handle_delete(self):
        if "/products/" in self.path:
            self.send_response(200)
            self.end_headers()
            product_id = self.path.split("/")[2]
            query = "delete from products where id=?"
            if exists(self.cursor, "products", product_id):
                self.wfile.write("Successfully deleted {0}".format(product_id).encode())
            else:
                self.wfile.write("Product with id {0} does not exist".format(product_id).encode())
            self.cursor.execute(query, (product_id,))
            self.conn.commit()

        if "/customers/" in self.path:
            self.send_response(200)
            self.end_headers()
            customer_id = self.path.split("/")[2]
            query = "delete from customers where id=?"
            if exists(self.cursor, "customers", customer_id):
                self.wfile.write("Successfully deleted {0}".format(customer_id).encode())
            else:
                self.wfile.write("Product with id {0} does not exist".format(customer_id).encode())
            self.cursor.execute(query, (customer_id,))
            self.conn.commit()

        if "/orders/" in self.path:
            self.send_response(200)
            self.end_headers()
            order_id = self.path.split("/")[2]
            query = "delete from orders where id=?"
            if exists(self.cursor, "order", order_id):
                self.wfile.write("Successfully deleted {0}".format(order_id).encode())
            else:
                self.wfile.write("Product with id {0} does not exist".format(order_id).encode())
            self.cursor.execute(query, (order_id,))
            self.conn.commit()

        if "/orders" == self.path:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Can't delete all orders")

        if "/products" == self.path:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Can't delete all products")
        if "/customers" == self.path:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Can't delete all customers")




def json_factory(cursor, row):
    json = {}
    for _id, col in enumerate(cursor.description):
        json[col[0]] = str(row[_id])
    return json


def run(server_class=HTTPServer, handler_class=RequestsHandler):
    conn = connect(r"C:\Projects\CloudComputing\Homework2\bd")
    conn.row_factory = json_factory
    handler_class.conn = conn
    handler_class.cursor = handler_class.conn.cursor()
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()