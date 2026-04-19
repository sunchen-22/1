import json
import asyncio
import urllib.request
import ssl

API_KEY = "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"

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

PREPROCESS = "Clean this message: fix typos, expand abbreviations, standardize format. Return only the result: {msg}"
CLASSIFY = """Return valid JSON only. category must be technical/billing/general/complaint:
{{"category":"","product":"","issue":"","urgency":"low/medium/high"}}
Message: {msg}"""

TECH = "This is a technical issue. Provide clear troubleshooting steps: {d}"
BILL = "Handle billing/refund request according to policy: {d}"
COMPLAIN = "Respond to complaint with empathy and escalate the ticket: {d}"
GENERAL = "Answer this general inquiry politely: {d}"

EVAL = "Evaluate this support response. Return JSON {{score:1-10, feedback:improvement tips}}: {r}"
IMPROVE = "Improve this response: original={r} feedback={f}"

class Processor:
    async def chain(self, msg):
        print("\n=== PROMPT CHAIN 1/3: Preprocessing")
        clean = llm(PREPROCESS.format(msg=msg))
        print("Result:", clean)

        print("\n=== PROMPT CHAIN 2/3: Classification")
        cls = llm(CLASSIFY.format(msg=clean))
        try:
            cls = json.loads(cls)
        except:
            cls = {"category":"general","product":"unknown","issue":clean,"urgency":"medium"}
        print("Classification:", cls)

        print("\n=== PROMPT CHAIN 3/3: Initial Response")
        init = llm(f"Generate a support response: {cls}")
        return clean, cls, init

    async def parallel(self, clean):
        print("\n=== PARALLEL TASKS: Sentiment + Keywords")
        sent = llm(f"Analyze sentiment: positive/negative/neutral: {clean}")
        kw = llm(f"Extract 3 key keywords: {clean}")
        print("Sentiment:", sent, "| Keywords:", kw)

    async def route(self, cls):
        print(f"\n=== ROUTING TO: {cls['category']}")
        if cls["category"] == "technical": return llm(TECH.format(d=cls))
        if cls["category"] == "billing": return llm(BILL.format(d=cls))
        if cls["category"] == "complaint": return llm(COMPLAIN.format(d=cls))
        return llm(GENERAL.format(d=cls))

    async def reflect(self, resp):
        print("\n=== REFLECTION 1/2: Evaluation")
        eval_res = llm(EVAL.format(r=resp))
        try:
            eval_data = json.loads(eval_res)
        except:
            eval_data = {"score":6,"feedback":"more friendly and concise"}

        print("\n=== REFLECTION 2/2: Improvement")
        improved = llm(IMPROVE.format(r=resp, f=eval_data["feedback"]))
        return resp, improved

    async def run(self, msg):
        print("="*50)
        print("PROCESSING TICKET:", msg)
        print("="*50)

        clean, cls, _ = await self.chain(msg)
        await self.parallel(clean)
        routed = await self.route(cls)
        orig, improved = await self.reflect(routed)

        print("\n✅ PROCESS COMPLETED!")
        print("BEFORE REFLECTION:", orig)
        print("AFTER REFLECTION:", improved)

if __name__ == "__main__":
    test_msg = "My app crashes when I open it"
    asyncio.run(Processor().run(test_msg))