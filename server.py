import asyncio
import secrets

from tinydb import TinyDB, Query
from PIL import Image

import tornado.ioloop
import tornado.web

database = TinyDB('database.json')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("templates/main.html", name="CoolBoard")

boards = {
	'all' : {
		'name' : "All Boards",
	},
	'b' : {
		'name' : "Off Topic",
	},
	'lfp' : {
		'name' : "Leftist Politics",
	},
	'gd' : {
		'name' : "Game Development",
	},
	'kno' : {
		'name' : "Philosophy/Literature",
	},
	'cyb' : {
		'name' : "Cyber Security",
	},
	'bwl' : {
		'name' : "Bowling",
	},
	'hrn' : {
		'name' : "Horny Posting",
	},
}

class BoardHandler(tornado.web.RequestHandler):
    def get(self, boardTag):
    	if boardTag == "all" or not boardTag:
    		boardTag = "all"
    		self.render("templates/catalog.html",
        		name = "CoolBoard",
        		boardTag = boardTag,
        		board = boards[boardTag]['name'],
        		threadList = database.all(),
        		boardList = boards,
        	)
    	else:
    		thread = Query()
    		self.render("templates/catalog.html",
       			name = "CoolBoard",
        		boardTag = boardTag,
        		board = boards[boardTag]['name'],
       			threadList = database.search(thread.board == boardTag),
        		boardList = boards,
        	)

class ThreadHandler(tornado.web.RequestHandler):
	def get(self, idNum):
		if not idNum.isdigit():
			return self.write("This thread number isn't valid.")

		threadData = database.get(doc_id = int(idNum))

		if not threadData:
			return self.write("This thread no longer exists.")

		boardTag = threadData['board']
		self.render("templates/thread.html",
        	name = "CoolBoard",
        	boardTag = boardTag,
        	board = boards[boardTag]['name'],
        	thread = threadData,
        	boardList = boards,
        )

fileWhitelist = [
	".png", ".jpg", ".jpeg", ".gif",
]

class CreateThread(tornado.web.RequestHandler):
	def post(self):
		if self.get_body_argument("title") == "":
			return self.write("You didn't give your thread a name!")

		boardTag = self.get_body_argument("board")
		if not boardTag in boards:
			return self.write("We get it, you know how to use inspect element.")

		if not self.request.files:
			return self.write("You didn't give your thread a file!")

		fileData = self.request.files['file'][0]
		fileExtension = "." + fileData['filename'].split(".")[-1]
		fileName = secrets.token_urlsafe(20) + fileExtension

		if not fileExtension in fileWhitelist:
			return self.write("The file type \'" + fileExtension + "\' is not supported.")

		id = database.insert({
			'title' : self.get_body_argument("title"),
			'text' : self.get_body_argument("body"),
			'file' : fileName,
			'replys' : [],
			'board' : boardTag,
		})

		outputFile = open("uploads/" + fileName, 'wb')
		outputFile.write(fileData['body'])

		thumb = Image.open("uploads/" + fileName)
		thumb.thumbnail((200, 200))
		thumb.save("thumbnails/" + fileName)

		self.redirect("/thread/" + str(id))

class ThreadReply(tornado.web.RequestHandler):
	def post(self, threadID):
		if self.get_body_argument("body") == "" and not self.request.files:
			return self.write("You have to post a file or some text!")

		if not self.request.files:
			fileName = ""
		else:
			fileData = self.request.files['file'][0]
			fileExtension = "." + fileData['filename'].split(".")[-1]
			fileName = secrets.token_urlsafe(20) + fileExtension

			if not fileExtension in fileWhitelist:
				return self.write("The file type \'" + fileExtension + "\' is not supported.")

			outputFile = open("uploads/" + fileName, 'wb')
			outputFile.write(fileData['body'])

			thumb = Image.open("uploads/" + fileName)
			thumb.thumbnail((200, 200))
			thumb.save("thumbnails/" + fileName)

		replyData = {
			'text' : self.get_body_argument("body"),
			'file' : fileName,
		}

		replysArray = database.get(doc_id = int(threadID))['replys']
		replysArray.append(replyData)

		database.update({'replys' : replysArray}, doc_ids=[int(threadID)])

		self.redirect("/thread/" + threadID)

def make_app():
    return tornado.web.Application([
        (r"/(\w{0,3})/?", BoardHandler),
        (r"/thread/(.*)", ThreadHandler),

        (r"/createThread", CreateThread),
        (r"/reply/(.*)", ThreadReply),

        (r"/uploads/(.*)", tornado.web.StaticFileHandler, {'path':'uploads/'}),
        (r"/thumbnails/(.*)", tornado.web.StaticFileHandler, {'path':'thumbnails/'}),

        (r"/static/(.*)", tornado.web.StaticFileHandler, {'path':'static/'}),
    ])

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
