from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

# Employee PINs
PIN_MAP = {
    "1978": {"user_id": 4, "name": "Нодира"},
    "7777": {"user_id": 22, "name": "Абдуллах"},
    "0405": {"user_id": 26, "name": "Ахрор"},
    "1360": {"user_id": 21, "name": "Байрам"},
    "4285": {"user_id": 25, "name": "Билол"},
    "2323": {"user_id": 18, "name": "Жасур Урынбаев"},
    "1111": {"user_id": 24, "name": "Камрон"},
    "2010": {"user_id": 5, "name": "Мирахмад Мирсагатов"},
    "2007": {"user_id": 16, "name": "Мирсадык"},
    "2000": {"user_id": 27, "name": "Нажмиддин"},
    "0814": {"user_id": 19, "name": "Нурсултан"},
}

# Telegram bot config
BOT_TOKEN = "8346861590:AAHgIe2cog_Z8rcbb4HoJEAvESPYd0w5Z6w"
TELEGRAM_CHAT_ID = "-4850637353"

# Poster API config
POSTER_TOKEN = "664212:0943952407a90a0dffb58c7903984f19"
SPOT_TABLET_ID = 1


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/delete", methods=["POST"])
def delete_transaction():
    transaction_id = request.form.get("transaction_id")
    new_transaction_id = request.form.get("new_transaction_id")
    reason = request.form.get("reason")
    pin = request.form.get("pin")

    if not transaction_id or not reason or not pin:
        return jsonify({"status": "error", "message": "Заполните все обязательные поля"})

    # Check PIN
    user_info = PIN_MAP.get(pin)
    if not user_info:
        return jsonify({"status": "error", "message": "Неверный PIN"})

    user_id = user_info["user_id"]

    # Step 1: Check if transaction exists
    check_url = f"https://coffee-n-1.joinposter.com/api/dash.getTransaction?token={POSTER_TOKEN}&transaction_id={transaction_id}"
    try:
        check_resp = requests.get(check_url)
        check_resp.raise_for_status()
        check_data = check_resp.json()
        if not check_data.get("response"):
            return jsonify({"status": "error", "message": "Чек не найден или уже удалён!"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка проверки чека: {e}"})

    # Step 2: Delete transaction — success if HTTP 200
    delete_url = f"https://coffee-n-1.joinposter.com/api/transactions.removeTransaction?token={POSTER_TOKEN}"
    payload = {
        "spot_tablet_id": SPOT_TABLET_ID,
        "transaction_id": transaction_id,
        "user_id": user_id,
        "comment": reason
    }
    if new_transaction_id:
        payload["new_transaction_id"] = new_transaction_id

    try:
        del_response = requests.post(delete_url, data=payload)
        if del_response.status_code == 200:
            # Always treat as success
            msg = (
                f"✅ Чек удалён\n"
                f"ID чека: {transaction_id}\n"
                f"Сотрудник: {user_info['name']}\n"
                f"PIN: {pin}\n"
                f"Причина: {reason}"
            )
            if new_transaction_id:
                msg += f"\nНовый ID чека: {new_transaction_id}"
            send_telegram_message(msg)
            return jsonify({"status": "success", "message": "Чек успешно удалён"})
        else:
            return jsonify({"status": "error", "message": f"Ошибка Poster API: {del_response.text}"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Ошибка удаления чека: {e}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
