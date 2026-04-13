"""
translate_kb.py -- 批量翻译 tools_kb JSON 文件，添加 zh_* 字段。
用法：
    set ANTHROPIC_API_KEY=sk-ant-...
    python scripts/translate_kb.py
增量模式：已有 zh_description 的文件自动跳过。
"""
import json, os, time
from pathlib import Path

try:
    import anthropic
except ImportError:
    raise SystemExit("请先安装：pip install anthropic")

ROOT_DIR = Path(__file__).parent.parent
KB_DIR   = ROOT_DIR / "data" / "tools_kb"
client   = anthropic.Anthropic()  # 自动读取 Claude Code 注入的 key
MODEL    = "claude-haiku-4-5-20251001"


def translate_list(items: list, context: str = "") -> list:
    if not items:
        return items
    payload = json.dumps(items, ensure_ascii=False)
    prompt = (
        "将以下 JSON 字符串数组从英文翻译成简体中文。"
        "要求：自然流畅，无翻译腔；AI工具专业术语准确；"
        "公司名/产品名/模型名保留英文（如 OpenAI、GPT-4、API）；"
        "数组长度必须与原文完全一致。"
        "直接返回 JSON 数组，不要加任何解释。\n\n" + payload
    )
    msg = client.messages.create(
        model=MODEL, max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    text = msg.content[0].text.strip()
    # 去掉可能的 markdown 代码块
    if text.startswith("```"):
        text = "\n".join(text.splitlines()[1:])
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        result = json.loads(text)
        if isinstance(result, list) and len(result) == len(items):
            return result
    except json.JSONDecodeError:
        pass
    # fallback: 按行拆分
    lines = [l.strip().strip('"').rstrip('",') for l in text.splitlines() if l.strip() and l.strip() not in ('[]', '[', ']')]
    return lines if lines else items


def translate_str(text: str) -> str:
    if not text:
        return text
    prompt = (
        "将以下英文文本翻译成简体中文。"
        "要求：自然流畅，无翻译腔；AI工具专业术语准确；"
        "公司名/产品名/模型名保留英文。"
        "直接返回翻译结果，不要加任何解释。\n\n" + text
    )
    msg = client.messages.create(
        model=MODEL, max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text.strip()


def translate_file(path: Path) -> bool:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if data.get("zh_description") and data.get("zh_plans") and data.get("zh_tags"):
        return False  # 已翻译，跳过

    name = data.get("name", path.stem)
    print(f"  翻译 {name}...", end=" ", flush=True)

    data["zh_tagline"]     = translate_str(data.get("tagline", ""))
    data["zh_description"] = translate_str(data.get("description", ""))
    data["zh_features"]    = translate_list(data.get("features", []))
    data["zh_pros"]        = translate_list(data.get("pros", []))
    data["zh_cons"]        = translate_list(data.get("cons", []))

    # Translate plan highlights
    plans = data.get("pricing", {}).get("plans", [])
    zh_plans = []
    for plan in plans:
        zh_plan = dict(plan)
        zh_plan["zh_highlights"] = translate_list(plan.get("highlights", []))
        zh_plans.append(zh_plan)
    data["zh_plans"] = zh_plans

    # Translate tags
    data["zh_tags"] = translate_list(data.get("tags", []))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("完成")
    time.sleep(0.5)  # 避免触发速率限制
    return True


def main():
    files = sorted(KB_DIR.glob("*.json"))
    done = skipped = failed = 0
    for p in files:
        try:
            if translate_file(p):
                done += 1
            else:
                skipped += 1
                print(f"  跳过 {p.stem}（已有中文内容）")
        except Exception as e:
            failed += 1
            print(f"  ✗ {p.stem} 失败：{e}")
    print(f"\n完成：{done} 个已翻译，{skipped} 个跳过，{failed} 个失败")
    if done > 0:
        print("现在运行：python scripts/build_tools.py")


if __name__ == "__main__":
    main()
