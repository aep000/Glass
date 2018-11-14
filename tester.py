from Glass import Glass
from Glass import Route

s = Glass()


def testRoute(request,response):
    print request.params
    response.body = str(request.params)
    return response

r =  Route("/",testRoute)

s.add_route(r)

s.run()