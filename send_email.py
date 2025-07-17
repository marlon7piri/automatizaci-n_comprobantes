import smtplib
EMAIL_USER = "marlon7piri@gmail.com"
EMAIL_PASS = "ywyu pgex nuex gwqs"

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.set_debuglevel(1)
    smtp.login(EMAIL_USER, EMAIL_PASS)
    print("Login OK")
