import telebot
from keep_alive import keep_alive
import pdfplumber
from io import BytesIO
from get_questions import get_questions

GRADE_LEVEL_MAP = {
    "صعب😬": "hard",
    "متوسط🙄": "medium",
    "سهل🤙": "easy"
}
bot = telebot.TeleBot("6982141096:AAFpEspslCkO0KWNbONnmWjUU_87jib__g8")


def send_user_details(chat_id, user):
    user_details = f"New user started ChatBot:\n\nUsername: @{user.username}\nFirst Name: {user.first_name}\nLast Name: {user.last_name}\nUser ID: {user.id}"
    bot.send_message(chat_id, user_details)
    
@bot.message_handler(commands=['feedback'])
def handle_feedback(message):
    feedback_prompt = "شكرًا لاستخدام البوت! 😊\n" \
                      "هل ترغب في مشاركة أفكارك أو ملاحظاتك لتحسين البوت؟ يرجى كتابة رسالتك هنا، فسأكون سعيدًا بسماع ما لديك!"
    bot.send_message(message.chat.id, feedback_prompt)
    # Register the next step handler to wait for the user's feedback
    bot.register_next_step_handler(message, handle_single_feedback)

def handle_single_feedback(message):
    feedback_text = message.text
    if feedback_text:
        # Send the feedback to your chat
        bot.send_message(854578633, f"New feedback from @{message.from_user.username}:\n{feedback_text}")
        bot.reply_to(message, "شكرا لك على ملاحظاتك! تم إرسالها بنجاح لتقديمها والعمل عليها.")
    else:
        bot.reply_to(message, "يرجى كتابة رسالة للملاحظات.")
        
@bot.message_handler(commands=['help'])
def handle_help(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("تواصل📞", url="https://t.me/RefOoSami"))
    help_text = """
    مرحبًا بك في مركز المساعدة ! 🤖📚

    إليك الأوامر المتاحة:
    /start - بدء البوت
    /feedback - تقديم ملاحظاتك أو الإبلاغ عن مشاكل
    /help - عرض هذه الرسالة للمساعدة

    لإنشاء اختبار، اتبع الخطوات التالية:
    1. أرسل محتوى المحاضرة كنص أو ملف PDF.
    2. اختر عدد الأسئلة التي تريد تضمينها.
    3. حدد مستوى الصعوبة (سهل، متوسط، أو صعب).
    4. انتظر حتى يقوم البوت بإنشاء أسئلة الاختبار استنادًا إلى ما قمت بتحديده.

    إذا كان لديك أي استفسارات أو تحتاج إلى مساعدة، فلا تتردد في التواصل! 😊
    """
    bot.reply_to(message, help_text, reply_markup=markup)
    
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 2  # Set row width to 2 for two buttons in each row
    markup.add(telebot.types.InlineKeyboardButton("أنشاء اختبار🫣", callback_data="start_quiz"),
                telebot.types.InlineKeyboardButton("تواصل📞", url="https://t.me/RefOoSami"))
    bot.send_message(message.chat.id, "اهلا بيك\ي👋😍\nاضغط/ي علي 'انشاء اختبار' للبدء😋", reply_markup=markup)
    # send_user_details(854578633, message.from_user)
    
@bot.callback_query_handler(func=lambda call: call.data == "start_quiz")
def start_quiz(call):
    chat_id = call.message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("نص في رسالة📝", "ملف PDF📂")
    bot.send_message(chat_id, "كيف ترغب في إرسال المحاضرة؟🤔", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "نص في رسالة📝")
def send_lecture_as_text(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "برجاء ارسال موضوع المحاضرة في رسالة📝")
    bot.register_next_step_handler(message, get_topic)

@bot.message_handler(func=lambda message: message.text == "ملف PDF📂")
def send_lecture_as_pdf(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "برجاء ارسال ملف PDF📂")
    bot.register_next_step_handler(message, get_topic_from_pdf)

def get_topic(message):
    topic = message.text
    bot.send_message(message.chat.id, "كم سؤال تريد انشاءه❓")
    bot.register_next_step_handler(message, lambda msg: get_num_questions(msg, topic))

def get_num_questions(message, topic):
    try:
        unicode_text = arabic_to_unicode(message.text)
        num_questions = int(unicode_text)
        if num_questions != 0:
            bot.send_message(message.chat.id, "اختر مستوي الصعوبه😌", reply_markup=create_grade_level_keyboard())
            # Register the next step handler to get the grade level choice
            bot.register_next_step_handler(message, lambda msg: get_grade_level(msg, topic, num_questions))
        else:
            bot.send_message(message.chat.id, "عدد الأسئلة يجب أن يكون اكبر من صفر 😢")
            bot.register_next_step_handler(message, lambda msg: get_num_questions(msg, topic))
    except (TypeError, ValueError):
        bot.send_message(message.chat.id, "برجاء اختيار رقم صحيح 🫣")
        bot.register_next_step_handler(message, lambda msg: get_num_questions(msg, topic))

def get_topic_from_pdf(message):
    if message.document:
        # Check if the provided file is a PDF
        if message.document.mime_type == 'application/pdf':
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            # Open the PDF using pdfplumber
            with pdfplumber.open(BytesIO(downloaded_file)) as pdf:
                page_count = len(pdf.pages)

                # Ask the user which pages they want to extract text from
                bot.reply_to(message, f"الملف يحتوي على {page_count} صفحة. يرجى تقديم أرقام الصفحات أو النطاقات (على سبيل المثال، 13-17)😊")

                # Register the next step handler to get the selected pages
                bot.register_next_step_handler(message, lambda msg: extract_text_from_pages(msg, pdf))
        else:
            # Inform the user that the provided file is not a PDF
            bot.reply_to(message, "الملف الذي قمت بإرساله ليس من نوع PDF. برجاء إرسال ملف PDF.")
            bot.register_next_step_handler(message, get_topic_from_pdf)
    else:
        # If the message does not contain a document, inform the user to upload a PDF file
        bot.reply_to(message, "الرجاء إرسال ملف PDF.")
        bot.register_next_step_handler(message, get_topic_from_pdf)
        
def extract_text_from_pages(message, pdf):
    initial_reply = bot.reply_to(message,'جاري استخراج البيانات برجاء الانتظار⌛')
    selected_pages = message.text.strip().split(',')
    extracted_text = ''
    invalid_input = False

    for page_range in selected_pages:
        if '-' in page_range:
            start, end = map(int, page_range.split('-'))
            if 1 <= start <= end <= len(pdf.pages):
                for i in range(start, end + 1):
                    extracted_text += pdf.pages[i - 1].extract_text()
            else:
                # Handle the case where the specified page range is invalid
                bot.send_message(message.chat.id, f"النطاق {page_range} غير صالح. يرجى تقديم نطاق صحيح.")
                invalid_input = True
                break
        else:
            page_num = int(page_range)
            if 1 <= page_num <= len(pdf.pages):
                extracted_text += pdf.pages[page_num - 1].extract_text()
            else:
                # Handle the case where the specified page number is invalid
                bot.send_message(message.chat.id, f"الصفحة {page_num} غير موجودة في الملف. يرجى تقديم صفحة صالحة.")
                invalid_input = True
                break

    if not invalid_input:
        bot.delete_message(message.chat.id, initial_reply.message_id)
        # Proceed with the rest of the process (e.g., ask for the number of questions)
        bot.send_message(message.chat.id, "كم سؤال تريد انشاءه❓")
        bot.register_next_step_handler(message, lambda msg: get_num_questions(msg, extracted_text))
    else:
        bot.delete_message(message.chat.id, initial_reply.message_id)
        # Ask the user to resend valid pages or ranges
        bot.reply_to(message, "يرجى إعادة إرسال الصفحات أو النطاقات الصالحة.")
        bot.register_next_step_handler(message, lambda msg: extract_text_from_pages(msg, pdf))

def arabic_to_unicode(text):
    unicode_text = ""
    for char in text:
        if char.isdigit():
            # Convert Arabic numeral to Unicode character
            unicode_text += chr(int(char) + 1632)
        else:
            unicode_text += char
    return unicode_text

def create_grade_level_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("صعب😬", "متوسط🙄", "سهل🤙")
    return markup

def get_grade_level(message, topic, num_questions):
    grade_level_text = message.text
    grade_level = GRADE_LEVEL_MAP.get(grade_level_text)
    if grade_level:
        send_quiz(message, topic, num_questions, grade_level)
    else:
        bot.send_message(message.chat.id, "برجاء اختيار مستوي صعوبه مناسب!🤔")
        bot.register_next_step_handler(message, lambda msg: get_grade_level(msg, topic, num_questions))
    
def send_quiz(message, topic, num_questions, grade_level):
    # Send the wait message and GIF
    wait_message = bot.send_message(message.chat.id, "برجاء الانتظار قد يستغرق الامر مدة تصل الي دقيقة...\nجاري انشاء الاسئلة🫣")
    # Make the request to fetch the questions and answers
    parsed_data = get_questions(grade_level,num_questions,topic)
    # parsed_data = parse_data(data)
    bot.delete_message(message.chat.id, wait_message.message_id)
    # Send each question as a poll
    for question_number, question_data in parsed_data.items():
        question_text = question_data["text"]
        options = question_data["options"]
        correct_answer = question_data["answer"]
        
        # Prepare poll options
        options_list = [f"{key}. {value}" for key, value in options.items()]
        
        # Check if options are too long
        if any(len(option) > 100 for option in options_list):
            # Skip invalid poll
            continue
        
        # Send the poll
        bot.send_poll(
            chat_id=message.chat.id,
            question=question_text,
            options=options_list,
            is_anonymous=False,  # To show poll results to users
            type="quiz",  # Set poll type to quiz
            correct_option_id=list(options.keys()).index(correct_answer),  # Set the correct answer index
            open_period=0  # To disable the "open for" duration
        )
    # send_user_details(854578633, message.from_user)
@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    if message.text == "/start":
        start(message)
    else:
        # Handle other messages by starting the conversation again
        start(message)

if __name__ == "__main__":
    while True:
        try:
            keep_alive()
            bot.polling()
        except:
            pass
