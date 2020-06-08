from bottle import route


@route("/")
def hello():
    return "hello world"
