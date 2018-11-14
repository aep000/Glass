# Glass
Object Oriented web framework made using python sockets

## Example Usage
```python
from Glass import Server, Route
s = Server()

def testRoute(request,response):
    print request.params
    response.body = "Hello World"
    return response

r =  Route("/",testRoute)
s.add_route(r)
s.run()
```

