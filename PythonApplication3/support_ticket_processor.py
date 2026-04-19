import json
import asyncio
import urllib.request
import ssl

# ===================== 在这里填入你的 API Key =====================
API_KEY = "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"

# ===================== LLM 调用（纯Python原生，不用requests！） =====================
def llm(prompt):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = json.dumps({
        "model": "zhipu/glm-4-air",
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as f:
            res = json.loads(f.read().decode())
            return res["choices"][0]["message"]["content"].strip()
    except:
        return ""

# ===================== 提示词 =====================
PREPROCESS = "清理消息：修正错别字、展开缩写、标准化。只返回结果：{msg}"
CLASSIFY = """返回JSON，category只能是technical/billing/general/complaint：
{{"category":"","product":"","issue":"","urgency":"low/medium/high"}}
消息：{msg}"""

TECH = "技术问题，给排查步骤：{d}"
BILL = "账单退款处理：{d}"
COMPLAIN = "投诉处理，共情+升级：{d}"
GENERAL = "通用咨询回答：{d}"

EVAL = "评估客服回复，返回JSON{{score:1-10,feedback:建议}}：{r}"
IMPROVE = "优化回复：原={r} 建议={f}"

# ===================== 主程序 =====================
class Processor:
    async def chain(self, msg):
        print("\n=== 提示链 1/3：预处理")
        clean = llm(PREPROCESS.format(msg=msg))
        print("结果：", clean)

        print("\n=== 提示链 2/3：分类")
        cls = llm(CLASSIFY.format(msg=clean))
        try:
            cls = json.loads(cls)
        except:
            cls = {"category":"general","product":"unknown","issue":clean,"urgency":"medium"}
        print("分类：", cls)

        print("\n=== 提示链 3/3：初始响应")
        init = llm(f"生成回复：{cls}")
        return clean, cls, init

    async def parallel(self, clean):
        print("\n=== 并行任务：情感分析 + 关键词")
        sent = llm(f"情感：positive/negative/neutral：{clean}")
        kw = llm(f"提取3个关键词：{clean}")
        print("情感：", sent, "关键词：", kw)

    async def route(self, cls):
        print(f"\n=== 路由：{cls['category']}")
        if cls["category"] == "technical": return llm(TECH.format(d=cls))
        if cls["category"] == "billing": return llm(BILL.format(d=cls))
        if cls["category"] == "complaint": return llm(COMPLAIN.format(d=cls))
        return llm(GENERAL.format(d=cls))

    async def reflect(self, resp):
        print("\n=== 反思 1/2：评估")
        eval_res = llm(EVAL.format(r=resp))
        try:
            eval_data = json.loads(eval_res)
        except:
            eval_data = {"score":6,"feedback":"更友好简洁"}

        print("\n=== 反思 2/2：优化")
        improved = llm(IMPROVE.format(r=resp, f=eval_data["feedback"]))
        return resp, improved

    async def run(self, msg):
        print("="*50)
        print("处理工单：", msg)
        print("="*50)

        clean, cls, _ = await self.chain(msg)
        await self.parallel(clean)
        routed = await self.route(cls)
        orig, improved = await self.reflect(routed)

        print("\n✅ 完成！")
        print("优化前：", orig)
        print("优化后：", improved)

# ===================== 测试 =====================
if __name__ == "__main__":
    test_msg = "My app crashes when I open it"
    asyncio.run(Processor().run(test_msg))