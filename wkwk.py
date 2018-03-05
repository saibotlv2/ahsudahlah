import os
from urllib.parse import quote
import requests

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
	MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
	SourceGroup, SourceRoom
)

app = Flask(__name__)

MendoBot = LineBotApi('CQcg1+DqDmLr8bouXAsuoSm5vuwB2DzDXpWc/KGUlxzhq9MSWbk9gRFbanmFTbv9wwW8psPOrrg+mHtOkp1l+CTlqVeoUWwWfo54lNh16CcqH7wmQQHT+KnkNataGXez6nNY8YlahgO7piAAKqfjLgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('c116ac1004040f97a62aa9c3503d52d9')

@app.route("/callback", methods=['POST'])
def callback():
	# get X-Line-Signature header value
	signature = request.headers['X-Line-Signature']

	# get request body as text
	body = request.get_data(as_text=True)
	app.logger.info("Request body: " + body)

	# handle webhook body
	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		abort(400)

	return 'OK'
	
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	'''
	Message Handler
	'''
	text = event.message.text
	a,b = text.split(" ")
	
	if isinstance(event.source, SourceGroup):
		subject = MendoBot.get_group_member_profile(event.source.group_id,
                                                    event.source.user_id)
		set_id = event.source.group_id
	elif isinstance(event.source, SourceRoom):
		subject = MendoBot.get_room_member_profile(event.source.room_id,
                                                   event.source.user_id)
		set_id = event.source.room_id
	else:
		subject = MendoBot.get_profile(event.source.user_id)
		set_id = event.source.user_id
		
	def leave():
		'''
        Leave a chat room.
        '''
		if isinstance(event.source, SourceGroup):
			MendoBot.reply_message(
				event.reply_token, 
				TextSendMessage("Bye group.")
			)
			MendoBot.leave_group(event.source.group_id)
		
		elif isinstance(event.source, SourceRoom):
			MendoBot.reply_message(
				event.reply_token, 
				TextSendMessage("Bye room.")
			)
			MendoBot.leave_room(event.source.room_id)
		
		else:
			MendoBot.reply_message(
				event.reply_token,
				TextSendMessage(">_< can't do...")
			)

	def getprofile():
		'''
		Send display name and status message of a user.
		'''
		result = ("Display name: " + subject.display_name + "\n"
				  "Profile picture: " + subject.picture_url)
		try:
			profile = MendoBot.get_profile(event.source.user_id)
			if profile.status_message:
				result += "\n" + "Status message: " + profile.status_message
		except LineBotApiError:
			pass
		MendoBot.reply_message(
			event.reply_token,
			TextSendMessage(result)
		)
		
	def wolfram(query):
		'''
		Get answer from WolframAlpha.
		query (str): string to be queried
		simple (bool): if true, return result as image link
		'''

		# WolframAlpha AppID, obtained from developer.wolframalpha.com
		wolfram_appid = os.getenv('WOLFRAMALPHA_APPID', None)

		url = 'https://api.wolframalpha.com/v1/{}?i={}&appid={}'
		return requests.get(url.format(mode, quote(query), wolfram_appid)).text
	
	if text == '/help':
		MendoBot.reply_message(
			event.reply_token,
			TextSendMessage("Available commands:\n"
							"leave, profile, wolfram\n"
							"Use /help <command> for more information.")
		)

	elif text == '/help leave':
		MendoBot.reply_message(
			event.reply_token,
			TextSendMessage("/leave, leave group")
		)
			
	elif text == '/help profile':
		MendoBot.reply_message(
			event.reply_token,
			TextSendMessage("/profile, check profile")
		)
		
	elif text == '/help wolfram':
		MendoBot.reply_message(
			event.reply_token,
			TextSendMessage("/wolfram, use wolfram.")
		)
		
	elif text == '/leave':
		leave()
	
	elif text == '/profile':
		getprofile()
	
	elif text[1:].lower().strip().startswith('wolfram'):
		MendoBot.reply_message(
			event.reply_token,
			TextSendMessage(wolfram(b))
		)
		
	else:
		MendoBot.reply_message(
			event.reply_token,
			TextSendMessage(text)
		)
		
if __name__ == "__main__":
	
	port = int(os.getenv('PORT', 5000))
	app.run(host='0.0.0.0', port=port)