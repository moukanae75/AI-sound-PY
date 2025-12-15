import speech_recognition as sr
import os
import shutil
import time
import arabic_reshaper
from bidi.algorithm import get_display

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
    "مضغوط": [".zip", ".rar"],
}

def print_ar(text):
    """وظيفة لطباعة النص العربي بشكل صحيح في التيرمينال"""
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        print(bidi_text)
    except:
        print(text)

def listen_to_command(prompt="🎤 أنا أستمع..."):
    """وظيفة للاستماع إلى الصوت وتحويله لنص"""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print_ar(prompt)
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            return ""

    try:
        command = recognizer.recognize_google(audio, language="ar-MA")
        print_ar(f"🗣️ لقد قلت: {command}")
        return command.lower()
    except sr.UnknownValueError:
        print_ar("❌ لم أفهم الكلام بوضوح.")
        return ""
    except sr.RequestError:
        print_ar("❌ مشكلة في الاتصال بالإنترنت.")
        return ""

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
            print_ar(f"❌ تعذر إنشاء المجلد: {e}")
            return

    files = os.listdir(src)
    counter = 0
    
    # تحديد الامتدادات المطلوبة إذا كان الفلتر نوع ملف
    target_extensions = []
    if filter_query and filter_query in FILE_Types:
        target_extensions = FILE_Types[filter_query]
        print_ar(f"🔎 تصفية حسب النوع: {filter_query} ({target_extensions})")
    elif filter_query:
        print_ar(f"🔎 تصفية حسب الاسم: يحتوي على '{filter_query}'")
    else:
        print_ar("📦 نقل الكل")

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
        print_ar("📂 لم يتم العثور على ملفات مطابقة لنقلها.")
    else:
        print_ar(f"🎉 تمت العملية! تم نقل {counter} ملفات.")

def execute_task(command):
    """تحليل وتنفيذ الأوامر"""
    if not command: return True

    if "نقل" in command or "move" in command:
        print_ar("🔄 بدأت عملية النقل...")

        # 1. المصدر
        source_path = get_path_from_name(command)
        if not source_path:
            response = listen_to_command("📂 من أي مجلد؟ (التنزيلات، الصور...)")
            source_path = get_path_from_name(response)
        
        if not source_path:
            print_ar("❌ لم أتعرف على المصدر.")
            return True

        # 2. الوجهة
        response = listen_to_command(f"📂 من {os.path.basename(source_path)}، إلى أين؟")
        dest_path = get_path_from_name(response)

        if not dest_path:
            print_ar("❌ لم أتعرف على الوجهة.")
            return True

        # 3. تحديد الملفات (الكل أو محدد)
        filter_query = None
        choice = listen_to_command("❓ هل تريد نقل **الكل** أم ملفات **محددة**؟")
        
        if "محدد" in choice or "specific" in choice or "بعض" in choice or "واحد" in choice:
            filter_query = listen_to_command("⌨️ ما هو اسم الملف أو نوعه؟ (مثال: 'صور'، 'تقرير')...")
            if not filter_query:
                print_ar("⚠️ لم أسمع الاسم، سأقوم بإلغاء العملية.")
                return True
        
        # 4. التنفيذ
        move_files(source_path, dest_path, filter_query)

    elif "خروج" in command or "exit" in command:
        print_ar("👋 وداعاً")
        return False
    
    else:
        print_ar("⚠️ أمر غير معروف.")
    
    return True

if __name__ == "__main__":
    print_ar("🤖 المساعد الذكي يعمل... (جرب قول 'نقل الملفات')")
    running = True
    while running:
        cmd = listen_to_command()
        if cmd:
            running = execute_task(cmd)
 
