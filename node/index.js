var http = require("http")
var log = require("./Log.js")
function print(x) {
	console.log(x)
}
var server = http.createServer(function(req, res){
	res.writeHead(200, {'Content-Type': 'text/plain'});
	res.write("Salut");
	log.info("info");
	res.end();
})

server.listen(5000)