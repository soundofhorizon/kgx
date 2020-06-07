from bottle import route, run

@route("/")
def hello():
        return "hello world"