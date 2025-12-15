import speech_recognition as sr
import os
import shutil
import time
import arabic_reshaper
from bidi.algorithm import get_display
from gtts import gTTS
from playsound import playsound
import uuid

# --- إعدادات المسارات ---
USER_HOME = os.path.expanduser("~")
KNOWN_PATHS = {
    "تنزيلات": os.path.join(USER_HOME, "Downloads"),
    "downloads": os.path.join(USER_HOME, "Downloads"),
    "صور": os.path.join(USER_HOME, "Pictures"),
    "pictures": os.path.join(USER_HOME, "Pictures"),
    "مستندات": os.path.join(USER_HOME, "Documents"),
    "documents": os.path.join(USER_HOME, "Documents"),
    "سطح المكتب": os.path.join(USER_HOME, "Desktop"),
    "desktop": os.path.join(USER_HOME, "Desktop"),
    "فيديو": os.path.join(USER_HOME, "Videos"),
    "videos": os.path.join(USER_HOME, "Videos"),
    "موسيقى": os.path.join(USER_HOME, "Music"),
    "music": os.path.join(USER_HOME, "Music"),
}

# --- أنواع الملفات المعروفة ---
FILE_Types = {
    "صور": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "فيديو": [".mp4", ".mkv", ".avi", ".mov"],
    "videos": [".mp4", ".mkv", ".avi", ".mov"],
    "مستندات": [".pdf", ".docx", ".txt", ".xlsx", ".pptx"],
    "documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx"],
    "صوت": [".mp3", ".wav"],
    "audio": [".mp3", ".wav"],
}

class TaskCancelled(Exception):
    """استثناء لإلغاء المهمة الحالية"""
    pass

def print_ar(text):
    """وظيفة لطباعة النص العربي بشكل صحيح في التيرمينال"""
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        print(bidi_text)
    except:
        print(text)

def speak(text):
    """تحويل النص إلى صوت وتشغيله"""
    print_ar(text) # طباعة النص أيضاً
    try:
        tts = gTTS(text=text, lang='ar')
        # استخدام اسم ملف عشوائي لتجنب مشاكل القفل في ويندوز
        filename = f"voice_{uuid.uuid4().hex}.mp3"
        tts.save(filename)
        playsound(filename)
        # محاولة حذف الملف، إذا فشل (بسبب القفل) لا مشكلة كبيرة
        try:
            os.remove(filename)
        except:
            pass
    except Exception as e:
        print_ar(f"❌ خطأ في الصوت: {e}")

def check_cancellation(text):
    """فحص إذا كان المستخدم يريد إلغاء العملية"""
    if not text: return False
    cancel_words = ["إلغاء", "توقف", "cancel", "stop", "abort", "رجوع"]
    return any(word in text.lower() for word in cancel_words)

def listen_to_command(prompt=None):
    """وظيفة للاستماع إلى الصوت وتحويله لنص"""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        if prompt:
            speak(prompt)
        
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            # timeout=None يعني ينتظر للأبد حتى يسمع بداية كلام
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            return ""

    try:
        command = recognizer.recognize_google(audio, language="ar-MA")
        print_ar(f"🗣️ لقد قلت: {command}")
        return command.lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        speak("❌ مشكلة في الاتصال بالإنترنت.")
        return ""

def get_mandatory_input(prompt):
    """دالة تكرر السؤال حتى يتم الحصول على إجابة مفهومة
    تلبي طلب المستخدم: (لايرجع الى الاول حتى يفهم)"""
    # أول مرة نسأل
    response = listen_to_command(prompt)
    if response:
        if check_cancellation(response):
            raise TaskCancelled()
        return response
        
    # إذا لم نفهم، ندخل في حلقة تكرار
    while True:
        # نعيد السؤال أو ننبه المستخدم
        speak("عذراً، لم أسمعك جيداً. " + prompt)
        response = listen_to_command() # لا نعيد قراءة السؤال كل مرة لتجنب الإزعاج، فقط ننتظر الإجابة
        if response:
            if check_cancellation(response):
                raise TaskCancelled()
            return response

def get_path_from_name(text):
    """محاولة إيجاد مسار مجلد معروف"""
    if not text: return None
    for name, path in KNOWN_PATHS.items():
        if name in text:
            return path
    return None

def move_files(src, dest, filter_query=None):
    """نقل الملفات مع إمكانية الفلترة باسم معين أو نوع ملف"""
    if not os.path.exists(dest):
        try:
            os.makedirs(dest)
        except Exception as e:
            speak(f"❌ تعذر إنشاء المجلد: {e}")
            return

    files = os.listdir(src)
    counter = 0
    
    # تحديد الامتدادات المطلوبة إذا كان الفلتر نوع ملف
    target_extensions = []
    if filter_query and filter_query in FILE_Types:
        target_extensions = FILE_Types[filter_query]
        speak(f"🔎 تصفية حسب النوع: {filter_query}")
    elif filter_query:
        speak(f"🔎 تصفية حسب الاسم: يحتوي على {filter_query}")
    else:
        speak("📦 نقل الكل")

    print_ar(f"⏳ جاري النقل من {os.path.basename(src)} إلى {os.path.basename(dest)}...")
    
    for file in files:
        src_file = os.path.join(src, file)
        dest_file = os.path.join(dest, file)
        
        if os.path.isfile(src_file) and not file.startswith('.'):
            if file == os.path.basename(__file__): continue
            
            # منطق الفلترة
            should_move = False
            if not filter_query:
                should_move = True # نقل الكل
            elif target_extensions:
                # فلترة حسب الامتداد
                if any(file.lower().endswith(ext) for ext in target_extensions):
                    should_move = True
            else:
                # فلترة حسب الاسم
                if filter_query in file.lower():
                    should_move = True
            
            if should_move:
                try:
                    shutil.move(src_file, dest_file)
                    print_ar(f"✅ تم نقل: {file}")
                    counter += 1
                except Exception as e:
                    print_ar(f"❌ خطأ في نقل {file}: {e}")
    
    if counter == 0:
        speak("لم أجد ملفات مطابقة لنقلها.")
    else:
        speak(f"تمت العملية! تم نقل {counter} ملفات.")

def execute_task(command):
    """تحليل وتنفيذ الأوامر"""
    if not command: return True

    if "نقل" in command or "move" in command:
        speak("حسناً، سأقوم بنقل الملفات. (يمكنك قول 'إلغاء' في أي وقت)")

        try:
            # 1. المصدر
            source_path = get_path_from_name(command)
            if not source_path:
                # استخدام وظيفة الإدخال الإجباري
                while True:
                    response = get_mandatory_input("من أي مجلد تريد النقل؟ (التنزيلات، الصور...)")
                    source_path = get_path_from_name(response)
                    if source_path:
                        break # وجدنا المجلد، نخرج من الحلقة
                    speak("لم أتعرف على هذا المجلد. حاول مرة أخرى.")
            
            # 2. الوجهة
            dest_path = None
            while True:
                response = get_mandatory_input(f"من {os.path.basename(source_path)}، إلى أين تريد النقل؟")
                dest_path = get_path_from_name(response)
                if dest_path:
                    break
                speak("لم أتعرف على مجلد الوجهة. حاول مرة أخرى.")

            # 3. تحديد الملفات (الكل أو محدد)
            filter_query = None
            choice = get_mandatory_input("هل تريد نقل الكل أم ملفات محددة؟")
            
            if "محدد" in choice or "specific" in choice or "بعض" in choice or "واحد" in choice:
                filter_query = get_mandatory_input("ما هو اسم الملف أو نوعه؟")
            
            # 4. التنفيذ
            move_files(source_path, dest_path, filter_query)
        
        except TaskCancelled:
            speak("❌ تم إلغاء العملية بناءً على طلبك.")

    elif "خروج" in command or "exit" in command:
        speak("وداعاً! أراك لاحقاً.")
        return False
    
    else:
        speak("لم أفهم هذا الأمر. ماذا تريد مني أن أفعل؟")
    
    return True

if __name__ == "__main__":
    speak("مرحباً بك. أنا جاهز للعمل.")
    running = True
    while running:
        # هنا ننتظر حتى نسمع أمراً
        cmd = listen_to_command()
        if cmd:
            running = execute_task(cmd)
