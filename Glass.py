import socket

class Glass:
    def __init__(self, ip="127.0.0.1", port=5000):
        self.ip=ip
        self.port = port
        self.routes = dict()
        self.errorRoutes = dict()
        self.__set_default_errors()

    def __set_default_errors(self):
        self.errorRoutes['404'] = Response("404 Page Not Found",'404',"Resource Not Found")
        self.errorRoutes['500'] = Response("500 Server Error", '500', "Server Error")

    def add_route(self, route):
        self.routes[route.path] = route
        return True

    def set_error_code(self, code, response):
        self.errorRoutes[code] = response

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        s.bind((self.ip, self.port))
        s.listen(5)
        while True:
            # Establish connection with client.
            c, addr = s.accept()
            print 'Got connection from', addr
            raw_request = c.recv(1024)
            request = Request(raw_request)
            print request.resource
            if request.resource in self.routes:
                try:
                    resp = self.routes[request.resource].run_route(request, Response())
                except Exception as e:
                    resp = self.errorRoutes['500']

            else:
                # TODO MAKE ERROR WRAPPER
                resp = self.errorRoutes['404']


            # send status line
            c.send(resp.gen_status_line())
            #send Headers
            c.send(resp.gen_header_text())
            c.send('\n')
            #send Body
            c.send(resp.gen_body())


class Middleware:
    # TODO handle errors and redirs
    def __init__(self, func):
        self.func = func

    def __str__(self):
        return str(self.func)

    def run_middleware(self, request, response):
        return self.func(request, response)


class Route:

    def __init__(self, path, func):
        self.path = path
        self.func = func
        self.middleware = list()

    def __str__(self):
        return self.path+str(self.func)

    def add_middleware(self, middleware):
        self.middleware.append(middleware)

    def run_route(self, request,response):
        for m in self.middleware:
            response = m.run_middleware(request,response)
            #TODO check for fail
        return self.func(request,response)
        #TODO check for fail here too


class Request:
    def __init__(self, requesttext):
        # TODO handle malformed requests in try
        data = requesttext.splitlines()
        statusline = data[0]
        statusline = statusline.split(' ')
        self.method = statusline[0]
        self.resource = statusline[1]
        self.__process_path()
        self.version = statusline[2]
        headers = dict()
        c = 0
        for h in data[1:]:
            # print repr(h)
            if h == "":
                break
            h = h.split(":")
            headers[h[0]] = ''.join(h[1])
        self.body = ''.join(requesttext.splitlines(True)[len(headers)+1:])
        self.raw_headers = headers
        # print headers
        if("Cookie" in headers):
            self.__process_cookies()

    def __process_path(self):
        self.params = dict()
        temp = self.resource.split("?")
        self.resource = temp[0]
        if (len(temp) > 1):
            for param in temp[1].split("&"):
                p = param.split("=")
                self.params[p[0]] = p[1]

    def __process_cookies(self):
        self.cookies = dict()
        cookies = self.raw_headers["Cookie"].split(';')
        for c in cookies:
            c = c.split('=')
            c[0] = c[0].replace(' ', '')
            self.cookies[c[0]] = c[1]

    def __getitem__(self, item):
        return self.raw_headers[item]


class Response:
    def __init__(self, body = "", statuscode = '200', statustext = "OK"):
        self.body = body
        self.statuscode = statuscode
        self.statustext = statustext
        self.content_type = 'text/html; encoding=utf8'
        self.headers = list()

    def add_cookie(self, name, value, expires="", maxage=-1, domain="", path=""):
        if(maxage>=0):
            expire_string = "Max-Age="+str(maxage)+"; "
        else:
            expire_string = "Expires="+expires+"; "
        if(domain!=""):
            domain = "Domain="+domain+"; "
        if(path!=""):
            path = "Path="+path+"; "
        cookie_attribs=expire_string+domain+path
        cookie_string = "%s=%s; %s"% (name, value, cookie_attribs[:-2])
        self.headers.append(["Set-Cookie", cookie_string])

    def gen_status_line(self):
        return '%s %s %s\n' % ('HTTP/1.1', self.statuscode, self.statustext)

    def gen_header_text(self):
        self.headers.append(["Content-Type", self.content_type])
        self.headers.append(["Content-Length", len(self.body)])
        self.headers.append(["Connection", "close"])
        return ''.join('%s: %s\n' % (k, v) for k, v in self.headers).encode()

    def gen_body(self):
        return self.body