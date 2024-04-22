import http.server
import socketserver
import psycopg2
import redis
from psycopg2 import Error

# Database Connection
db_host = 'localhost'
db_name = 'redis-db'
db_user = 'postgres'
db_password = 'FAq1auyu@'

# Redis Connection
redis_host = 'localhost'
redis_port = 6379
redis_db = 0

redis_conn = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

class ProductsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Check if data exists in Redis
            redis_key = 'products'
            cached_html = redis_conn.get(redis_key)

            if cached_html:
                # Serve cached HTML from Redis
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(cached_html)
                print("Cache found and data displayed from Redis.")
            else:
                # Connect to the database
                connection = psycopg2.connect(user=db_user,
                                              password=db_password,
                                              host=db_host,
                                              database=db_name)
                cursor = connection.cursor()
                print("Cache could not found. Retrieving data from database.")

                # Create a query to select products
                select_query = "SELECT * FROM products;"

                # Execute the query
                cursor.execute(select_query)

                # Fetch all the results
                products = cursor.fetchall()

                # Generate HTML content
                html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Products</title>
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            border: 1px solid #dddddd;
            text-align: left;
            padding: 8px;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <h1>Products</h1>
    <table id="product-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Price</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>"""

                for product in products:
                    html_content += "<tr>"
                    html_content += "<td>{}</td>".format(product[0])
                    html_content += "<td>{}</td>".format(product[1])
                    html_content += "<td>${}</td>".format(product[2])
                    html_content += "<td>{}</td>".format(product[3])
                    html_content += "</tr>"

                html_content += """</tbody>
    </table>
</body>
</html>"""

                # Store HTML content in Redis with a 5-minute expiration
                redis_conn.setex(redis_key, 300, html_content.encode())

                # Send HTTP response
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(html_content.encode())

                # Close the connection
                if connection:
                    cursor.close()
                    connection.close()

        except (Exception, Error) as error:
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("Error: {}".format(error).encode())

# Set up HTTP server
def run():
    try:
        server_address = ('', 8000)
        httpd = socketserver.TCPServer(server_address, ProductsHandler)
        print("Server started at http://localhost:8000")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server shutting down.")
        httpd.socket.close()

if __name__ == '__main__':
    run()
