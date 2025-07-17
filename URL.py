import datetime
import getpass
import subprocess
import logging
import textwrap
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

# Recipients and sender
EMAIL_RECIPIENTS = ["rravi@akamai.com"]
FROM_EMAIL = f"{getpass.getuser()}@akamai.com"

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def wrap_text(text, width=100, indent="    "):
    """Wraps the given text to the specified width with indentation for wrapped lines."""
    return "\n".join(textwrap.wrap(text, width=width, subsequent_indent=indent))

def underline_text(text):
    """Underline the given text using ANSI escape sequences."""
    return f"\033[4m{text}\033[0m"

def generate_alert_urls():
    BASE_URL = (
        "https://testme.com/cgi-bin/reporter/alertreporter?"
        "__option_summary_collate_by=percent&report_type=instance_detail&__option_all_attributes=no&"
        "__option_over_time_groupby=hour&__option_over_time_groupby_definition=no&"
        "__option_over_time_use_graph=yes&__option_most_frequent_groupby=Alert+Instance+Key&"
        "__option_most_frequent_use_defs=no&__option_most_frequent_threshhold=50&__option_p1_thres=1&"
        "__option_p2_thres=20&__option_p3_p5_thres=50&__select_Active=1&__select_Category+ID={category_id}&"
        "__exact_Definition+ID=exact&__exact_Alert+Name=substring&__exact_Ecor+Number=exact&"
        "__exact_Region+Number=exact&__exact_Machine+IP=exact&__exact_Alert+Instance+Key=exact&"
        "__exact_Owner+Email=substring&__exact_Ticket+ID=exact&__exact_AMS+Alert+Definition+ID=exact&"
        "__dynamic_filter_=Install+Group&__exact_alert_data_value_1_=exact&__exact_alert_data_value_2_=exact&"
        "__exact_alert_data_value_3_=exact&__exact_alert_data_value_4_=exact&gmtoffset=19800&"
        "__time_options_=__use_start_&__month_From=7&__day_From=7&__year_From=2025&__hour_From=13&"
        "__min_From=41&__month_Until=7&__day_Until=10&__year_Until=2025&__hour_Until=13&__min_Until=41&"
        "__time_relation_Age=1&__time_unit_Age=Days&output_format=HTML&useNewWindow=on&timezone=gmt&"
        "datasource=Production&Action=Create%20Report"
    )

    CATEGORIES = {
        "dart alerts": "80",
        "scrub alerts": "91"
    }

    START_DATE = datetime.datetime.now()
    lines = []

    for i in range(5):
        start = START_DATE - datetime.timedelta(days=i)
        end = start + datetime.timedelta(days=1)

        for name, category_id in CATEGORIES.items():
            url_with_category = BASE_URL.format(category_id=category_id)
            parsed_url = urlparse(url_with_category)
            query = parse_qs(parsed_url.query)

            query["__month_From"] = [str(start.month)]
            query["__day_From"] = [str(start.day)]
            query["__year_From"] = [str(start.year)]
            query["__hour_From"] = [str(start.hour)]
            query["__min_From"] = [str(start.minute)]

            query["__month_Until"] = [str(end.month)]
            query["__day_Until"] = [str(end.day)]
            query["__year_Until"] = [str(end.year)]
            query["__hour_Until"] = [str(end.hour)]
            query["__min_Until"] = [str(end.minute)]

            new_query = urlencode(query, doseq=True)
            final_url = urlunparse(parsed_url._replace(query=new_query))

            underlined_url = underline_text(final_url)
            lines.append(f"{name.title()} (Date: {start.strftime('%Y-%m-%d')}):\n{underlined_url}\n")

    return "\n".join(lines)

# ================= EMAIL SENDING ==================

def send_output_via_sendmail(output_text: str):
    """Send the given output text via sendmail as the raw email body (no attachments)."""
    timestamp = get_timestamp()
    print("\n⚠️  You are about to send the output via email.")
    while True:
        confirm = input("Enter 1 to send email, 0 to skip sending: ").strip()
        if confirm == '1':
            break
        elif confirm == '0':
            print("❌ Email not sent. 👋 Exiting email sending step.")
            return
        else:
            print("Invalid input. Enter 1 (send) or 0 (skip).")

    to_emails = ", ".join(EMAIL_RECIPIENTS)
    subject = f"Akamai Service Log Report - {timestamp}"

    message = [
        f"Subject: {subject}",
        f"To: {to_emails}",
        f"From: {FROM_EMAIL}",
        "",
        f"Here are the logs for the Akamai services processed on {timestamp}:",
        "",
        output_text,
    ]

    email_body = "\n".join(message)

    try:
        with subprocess.Popen(["sendmail", "-t"], stdin=subprocess.PIPE, text=True) as proc:
            proc.stdin.write(email_body)
            proc.stdin.close()
            proc.wait()
        print(f"✅ Logs sent to {to_emails}. Script completed successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        logging.error(f"Failed to send email: {e}")

if __name__ == "__main__":
    alert_urls = generate_alert_urls()
    print(alert_urls)  # Optional: print URLs locally
    send_output_via_sendmail(alert_urls)

