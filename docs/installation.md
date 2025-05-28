نصب کتابخونه Baleh
برای استفاده از کتابخونه Baleh، مراحل زیر را دنبال کنید:

پیش‌نیازها
پایتون نسخه 3.7 یا بالاتر
دسترسی به اینترنت برای نصب بسته‌ها
نصب از PyPI
ترمینال یا خط فرمان را باز کنید.
دستور زیر را اجرا کنید:
bash

کپی
pip install baleh
برای به‌روزرسانی به آخرین نسخه:
bash

کپی
pip install baleh --upgrade
نصب از سورس کد
مخزن گیت‌هاب را کلون کنید:
bash

کپی
git clone https://github.com/hamidrashidi98/baleh.git
cd baleh
بسته را بسازید:
bash

کپی
python setup.py sdist bdist_wheel
نصب کنید:
bash

کپی
pip install dist/baleh-0.2.2.tar.gz
وابستگی‌ها
کتابخونه به این بسته‌ها نیاز داره:

aiohttp>=3.8.0
requests>=2.25.0
برای نصب وابستگی‌ها:

bash

کپی
pip install -r requirements.txt