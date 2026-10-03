"""
agents/topic_agent.py  --  the TOPIC AGENT

Job: read chunks of study material and return the important topics.

Input : a list of text chunks (from the Document Agent)
Output: a list of topics, for example
    {"id": "t1", "topic": "Registers", "importance": "High",
     "summary": "Small fast storage inside the CPU.",
     "key_concepts": ["EAX", "EBX", "general-purpose"], "mentions": 3}

How it works (simple "read in batches, then combine" idea):
  1. Group the chunks into batches that fit in one AI request.
  2. Ask the AI for the topics of each batch.
  3. Combine all batches in Python: merge duplicates, count mentions, rank.
"""
import json
import math
import re

from core.llm import ask_llm

MAX_CHARS_PER_BATCH = 6000   # how much text we send to the AI at once
MAX_BATCHES = 12             # if the document is huge, we sample evenly
IMPORTANCE_RANK = {"High": 3, "Medium": 2, "Low": 1}

SYSTEM_PROMPT = "You are an expert teacher who finds the key topics in study material."

PROMPT_TEMPLATE = """Read the study material below and list its main topics.

Rules:
- Return 3 to 8 topics.
- Use short topic names (1 to 4 words), like "Registers" or "Addressing Modes".
- Only use topics that appear in the text. Do not invent anything.
- importance must be exactly one of: High, Medium, Low.
- Return ONLY valid JSON, with no extra words and no markdown.

JSON format:
{{"topics": [
  {{"topic": "Topic name", "importance": "High",
    "summary": "One sentence explaining the topic.",
    "key_concepts": ["concept 1", "concept 2"]}}
]}}

STUDY MATERIAL:
\"\"\"
{text}
\"\"\"
"""


# ---------- Step 1: prepare the text ----------
def chunks_to_texts(chunks):
    """Accept plain strings OR dicts like {"text": "..."} from the Document Agent."""
    texts = []
    for c in chunks:
        text = c["text"] if isinstance(c, dict) else str(c)
        if text.strip():
            texts.append(text.strip())
    return texts


def make_batches(texts, max_chars=MAX_CHARS_PER_BATCH):
    """Group chunks into batches that are not bigger than max_chars."""
    batches, current, size = [], [], 0
    for t in texts:
        if current and size + len(t) > max_chars:
            batches.append("\n\n".join(current))
            current, size = [], 0
        current.append(t)
        size += len(t)
    if current:
        batches.append("\n\n".join(current))
    return batches


def sample_evenly(batches, max_batches=MAX_BATCHES):
    """If there are too many batches, pick evenly spaced ones across the document."""
    if len(batches) <= max_batches:
        return batches
    step = len(batches) / max_batches
    return [batches[int(i * step)] for i in range(max_batches)]


# ---------- Step 2: ask the AI and read its answer safely ----------
def parse_json(text):
    """Turn the AI's reply into a Python dict. Returns None if it can't."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")  # try to cut out the {...} part
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None


def clean_topic(raw):
    """Check one topic from the AI. Fix small problems, reject unusable ones."""
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("topic", "")).strip()
    if not name:
        return None
    importance = raw.get("importance", "Medium")
    if importance not in IMPORTANCE_RANK:
        importance = "Medium"
    concepts = raw.get("key_concepts", [])
    if not isinstance(concepts, list):
        concepts = []
    return {
        "topic": name,
        "importance": importance,
        "summary": str(raw.get("summary", "")).strip(),
        "key_concepts": [str(c).strip() for c in concepts if str(c).strip()],
    }


def extract_topics_from_batch(batch_text, llm_fn=ask_llm):
    """Ask the AI for the topics in ONE batch. Tries twice if the reply is broken."""
    prompt = PROMPT_TEMPLATE.format(text=batch_text)
    for _ in range(2):
        data = parse_json(llm_fn(prompt, SYSTEM_PROMPT))
        if isinstance(data, dict) and isinstance(data.get("topics"), list):
            topics = [clean_topic(t) for t in data["topics"]]
            return [t for t in topics if t]
    return []


# ---------- Step 3: combine all batches ----------
def _normalize(name):
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def merge_and_rank(topic_lists, max_topics=15):
    """Merge duplicate topics, count mentions, rank, and assign final importance."""
    merged = {}
    for t in topic_lists:
        key = _normalize(t["topic"])
        if key not in merged:
            merged[key] = dict(t, mentions=1, _best=IMPORTANCE_RANK[t["importance"]])
        else:
            m = merged[key]
            m["mentions"] += 1
            m["_best"] = max(m["_best"], IMPORTANCE_RANK[t["importance"]])
            for c in t["key_concepts"]:
                if c not in m["key_concepts"]:
                    m["key_concepts"].append(c)

    # A topic mentioned in many parts of the document is probably important.
    ranked = sorted(merged.values(), key=lambda m: m["mentions"] * 2 + m["_best"], reverse=True)
    ranked = ranked[:max_topics]

    n = len(ranked)
    high_cut, medium_cut = math.ceil(n * 0.3), math.ceil(n * 0.7)
    result = []
    for i, m in enumerate(ranked):
        importance = "High" if i < high_cut else "Medium" if i < medium_cut else "Low"
        result.append({
            "id": "t" + str(i + 1),
            "topic": m["topic"],
            "importance": importance,
            "summary": m["summary"],
            "key_concepts": m["key_concepts"],
            "mentions": m["mentions"],
        })
    return result


# ---------- The main functions ----------
def run_topic_agent(chunks, llm_fn=ask_llm, max_topics=15):
    """MAIN FUNCTION: chunks in, ranked list of topics out."""
    texts = chunks_to_texts(chunks)
    if not texts:
        raise ValueError("Topic Agent got no text. Did the Document Agent run first?")
    batches = sample_evenly(make_batches(texts))
    all_topics = []
    for batch in batches:
        all_topics.extend(extract_topics_from_batch(batch, llm_fn))
    return merge_and_rank(all_topics, max_topics)


def topic_agent_node(state, llm_fn=ask_llm):
    """Used by the orchestrator: reads state['chunks'], writes state['topics']."""
    if "chunks" not in state:
        raise ValueError("state has no 'chunks'. The Document Agent must run first.")
    state["topics"] = run_topic_agent(state["chunks"], llm_fn=llm_fn)
    return state
