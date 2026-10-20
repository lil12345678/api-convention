from app.ai_chat import chat_turn
from app.database import SessionLocal

def ask(messages):
    db = SessionLocal()
    try:
        result = chat_turn(db, messages[1:])
        for call in result["tool_calls"]:
            print(f"[工具] {call['name']} {json.dumps(call['arguments'], ensure_ascii=False)}")
        return result["reply"]
    except Exception as error:
        status = getattr(error, "status", None)
        raise SystemExit(f"{status or ''} {error}".strip()) from error
    finally:
        db.close()
        
def main():
    messages = [{"role": "system", "content": SYSTEM}]
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:]).strip()
        messages.append({"role": "user", "content": text})
        print(ask(messages))
        return

    print("输入内容后回车，空行退出。")
    while True:
        try:
            text = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            break
        messages.append({"role": "user", "content": text})
        reply = ask(messages)
        messages.append({"role": "assistant", "content": reply})
        print(f"助手：{reply}")


if __name__ == "__main__":
    main()
