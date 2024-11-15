from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from api.chatgpt import ChatGPT

import os

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
supported_languages = ["zh", "en", "vi", "km", "my"]  # gpt4o 支援的語言列表

working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"
admin_members = os.getenv("ADMIN_MEMBERS", default="").split(",") if os.getenv("ADMIN_MEMBERS") else []


app = Flask(__name__)
chatgpt = ChatGPT()

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global AI_GUIDELINES
    global working_status
    global supported_languages
    
    if event.message.type != "text":
        return
    
    user_id = event.source.user_id
    is_admin = user_id.strip() in [member.strip() for member in admin_members]

    if event.message.text == "說話":
        working_status = True
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我可以說話囉，歡迎來跟我互動 ^_^ "))
        return

    if event.message.text == "閉嘴":
        working_status = False
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「說話」 > <"))
        return
    
    # 特殊命令：查目前的環境變數值 (Debug)
    if event.message.text.lower() == "查目前的變數值" and is_admin:
        env_vars = {
            "OPENAI_MODEL": os.getenv("OPENAI_MODEL"),
            "OPENAI_TEMPERATURE": os.getenv("OPENAI_TEMPERATURE"),
            "OPENAI_FREQUENCY_PENALTY": os.getenv("OPENAI_FREQUENCY_PENALTY"),
            "OPENAI_PRESENCE_PENALTY": os.getenv("OPENAI_PRESENCE_PENALTY"),
            "OPENAI_MAX_TOKENS": os.getenv("OPENAI_MAX_TOKENS"),
            "MSG_LIST_LIMIT": os.getenv("MSG_LIST_LIMIT"),
            "INIT_LANGUAGE": os.getenv("INIT_LANGUAGE"),
            "AI_GUIDELINES": os.getenv("AI_GUIDELINES"),
            "ADMIN_MEMBERS": os.getenv("ADMIN_MEMBERS"),
            "supported_languages": ", ".join(supported_languages)
        }
        # 格式化環境變數為文本
        env_output = "\n".join([f"{key}: {value}" for key, value in env_vars.items()])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"目前的環境變數值:\n{env_output}")
        )
        return

    if event.message.text.lower().startswith("lang set ") and is_admin:
        requested_languages = event.message.text.lower().replace("lang set ", "").split(",")
        filtered_languages = [lang for lang in requested_languages if lang in supported_languages]
        if filtered_languages:
            AI_GUIDELINES = f"將所有輸入的訊息翻譯成{','.join(filtered_languages)}等語言，先列出語言如{','.join([f'【{lang}】' for lang in filtered_languages])}，後附上此語言翻譯結果，一種語言一行，僅執行翻譯，不進行其他互動或回答問題"
            chatgpt.reinit(new_guideline=AI_GUIDELINES)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"已設定 AI_GUIDELINES 為: {AI_GUIDELINES}")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入有效的語言代碼，例如: 'lang set vi,km,my,en'，目前支援的語言有: vi, km, my, en, zh-TW, ja, fr")
            )
        return

    # 特殊命令：顯示群組和用戶 ID
    if event.message.text.lower() == "show id":
        group_id = event.source.sender_id if event.source.type == "group" else "N/A"
        group_name = "N/A"
        if group_id != "N/A" and event.source.type == "group":
            try:
                group_summary = line_bot_api.get_group_summary(group_id)
                group_name = group_summary.group_name
            except Exception as e:
                group_name = "Unknown"
        user_profile = line_bot_api.get_profile(user_id)
        user_name = user_profile.display_name if user_profile else "Unknown"
        response = (f"user name: {user_name}\n"
                    f"user id: {user_id}\n"
                    f"group_name: {group_name}\n"
                    f"group_id: {group_id}\n"
                    f"is_admin: {is_admin}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
        return
        
    if working_status:
        # chatgpt.add_msg(f"HUMAN:{event.message.text}?\n")
        chatgpt.add_msg(f"{event.message.text} \n")
        reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        chatgpt.add_msg(f"AI:{reply_msg}\n")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))


if __name__ == "__main__":
    app.run()
