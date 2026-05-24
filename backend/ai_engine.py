import os
import re
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def get_text_llm():
    return ChatOpenAI(
        model="deepseek/deepseek-v4-flash",
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url=OPENROUTER_BASE_URL,
        temperature=0.7,
    )

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception)
)
def generate_content(topic: str, tone: str, audience: str, content_type: str, description: str = "") -> str:
    llm = get_text_llm()
    
    extra_instructions = f"\nAdditional Instructions: {description}" if description else ""
    
    if content_type.lower() == "blog":
        system_prompt = (
            "You are an expert SEO content strategist and blog writer. Produce a well-structured, engaging blog post. "
            "CRITICAL CONSTRAINTS: Use proper Markdown formatting (H1, H2s, bullet points). "
            "Do not include introductory conversational text (e.g., 'Here is your post'). Output only the blog content."
        )
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\n\nDraft the complete blog post."
    
    elif content_type.lower() == "linkedin":
        system_prompt = (
            "You are a top-tier B2B LinkedIn ghostwriter. Create an engaging, hook-driven LinkedIn post. "
            "CRITICAL CONSTRAINTS: Start with a strong, scroll-stopping hook. Use short, punchy paragraphs with white space. "
            "Integrate 2-4 relevant emojis naturally. End with a clear call-to-action and 3-5 targeted hashtags. "
            "Output only the post content without preamble."
        )
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\n\nDraft the LinkedIn post."
    
    elif content_type.lower() == "ad copy":
        system_prompt = (
            "You are a master direct-response copywriter. Write high-converting ad copy. "
            "CRITICAL CONSTRAINTS: Use the AIDA framework (Attention, Interest, Desire, Action). "
            "Focus heavily on user benefits rather than features. Keep it concise and highly persuasive. "
            "Output only the ad copy."
        )
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\n\nDraft the ad copy."

    elif content_type.lower() == "twitter thread":
        system_prompt = (
            "You are an expert Twitter growth hacker. Write a highly engaging, viral Twitter thread. "
            "CRITICAL CONSTRAINTS: Number each tweet explicitly (e.g., 1/5, 2/5). Start with a scroll-stopping hook. "
            "Keep sentences short and punchy. Do not include introductory text (e.g., 'Here is your thread'). "
            "Output only the thread content."
        )
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\n\nDraft the Twitter thread."

    elif content_type.lower() == "instagram caption":
        system_prompt = (
            "You are a top-tier Instagram growth specialist. Write a captivating caption designed for high engagement. "
            "CRITICAL CONSTRAINTS: Start with a strong hook on the first line. Use line breaks for readability. "
            "Integrate emojis naturally. End with a clear call-to-action and 5-10 relevant hashtags. "
            "Output only the caption without preamble."
        )
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\n\nDraft the Instagram caption."

    elif content_type.lower() == "facebook post":
        system_prompt = (
            "You are an expert community manager. Write a highly engaging Facebook post optimized for comments and shares. "
            "CRITICAL CONSTRAINTS: Keep the tone conversational and accessible. Structure the post to encourage a conversation, "
            "ending with a specific question or prompt for the audience. Output only the post text without introductory filler."
        )
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\n\nDraft the Facebook post."

    elif content_type.lower() == "email newsletter":
        system_prompt = (
            "You are a master email marketer. Write a compelling, high-converting email newsletter. "
            "CRITICAL CONSTRAINTS: The first line MUST be exactly 'Subject: [Your generated subject line]'. "
            "Use short paragraphs, clear subheadings if necessary, and end with a single, unmissable call-to-action (CTA). "
            "Output only the email content."
        )
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\n\nDraft the email newsletter."

    elif content_type.lower() == "product description":
        system_prompt = (
            "You are an elite e-commerce conversion copywriter. Write a persuasive, SEO-friendly product description. "
            "CRITICAL CONSTRAINTS: Focus heavily on emotional and practical benefits over raw technical features. "
            "Use a short introductory paragraph followed by bullet points for key features/benefits. End with a strong CTA. "
            "Output only the product description."
        )
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\n\nDraft the product description."

    elif content_type.lower() == "youtube script":
        system_prompt = (
            "You are an expert YouTube scriptwriter and audience retention strategist. Write a highly engaging video script. "
            "CRITICAL CONSTRAINTS: Format the output strictly with these capitalized section headers: [HOOK], [INTRO], [BODY], and [OUTRO]. "
            "Include brief visual or audio cues in brackets (e.g., [Upbeat music starts]). Focus on high pacing. "
            "Output only the formatted script."
        )
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\n\nDraft the YouTube script."

    elif content_type.lower() == "landing page":
        system_prompt = (
            "You are a conversion rate optimization (CRO) expert. Write high-converting landing page copy. "
            "CRITICAL CONSTRAINTS: Structure the output strictly as follows: 1) A clear, benefit-driven Hero Headline. "
            "2) A supporting Sub-headline. 3) 3-4 bullet points highlighting key benefits. 4) A strong, action-oriented Call to Action (CTA) button text. "
            "Output only the copy."
        )
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\n\nDraft the landing page copy."

    else:
        system_prompt = (
            "You are a professional marketing content creator. "
            "Provide highly polished, formatted text ready for immediate publication. Output only the requested content."
        )
        human_prompt = "Format: {content_type}\nTopic: {topic}\nTone: {tone}\nAudience: {audience}" + extra_instructions + "\n\nDraft the content."

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    chain = prompt | llm
    response = chain.invoke({"topic": topic, "tone": tone, "audience": audience, "content_type": content_type})
    return response.content

# --- LangGraph Content Improver ---

class GraphState(TypedDict):
    original_text: str
    goal: str
    analysis: str
    refined_text: str
    explanation: str

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
def analyze_text(state: GraphState):
    llm = get_text_llm()
    prompt = (
        f"You are an expert editorial director. Analyze the provided text against this specific improvement goal: '{state['goal']}'.\n\n"
        f"Text:\n{state['original_text']}\n\n"
        "Return a concise, bulleted list of 2-3 strict instructions on how to rewrite the text to meet this goal. "
        "Do not rewrite the text yet. Output only the analysis."
    )
    res = llm.invoke([HumanMessage(content=prompt)])
    return {"analysis": res.content}

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
def refine_text(state: GraphState):
    llm = get_text_llm()
    prompt = (
        f"Original text: {state['original_text']}\n\n"
        f"Editorial Analysis: {state['analysis']}\n\n"
        f"Rewrite the original text by applying the editorial analysis to perfectly achieve this goal: '{state['goal']}'.\n\n"
        "CRITICAL: Return ONLY the raw rewritten text. Do not wrap the output in markdown blocks, do not use quotes, and do not include any conversational filler."
    )
    res = llm.invoke([HumanMessage(content=prompt)])
    return {"refined_text": res.content}

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
def generate_explanation(state: GraphState):
    llm = get_text_llm()
    prompt = (
        f"Original text: {state['original_text']}\n"
        f"Refined text: {state['refined_text']}\n\n"
        f"You are a transparent editor. In exactly 2 concise sentences, explain the specific rhetorical, tonal, or structural changes you made to achieve the goal: '{state['goal']}'."
    )
    res = llm.invoke([HumanMessage(content=prompt)])
    return {"explanation": res.content}

improver_graph = StateGraph(GraphState)
improver_graph.add_node("analyze", analyze_text)
improver_graph.add_node("refine", refine_text)
improver_graph.add_node("explain", generate_explanation)

improver_graph.add_edge(START, "analyze")
improver_graph.add_edge("analyze", "refine")
improver_graph.add_edge("refine", "explain")
improver_graph.add_edge("explain", END)

improver_app = improver_graph.compile()

def improve_content(text: str, goal: str):
    state = {"original_text": text, "goal": goal}
    result = improver_app.invoke(state)
    return {
        "refined_text": result["refined_text"],
        "explanation": result["explanation"]
    }

# --- Image Generation ---

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception)
)
async def generate_matching_image(topic: str, tone: str, generated_text: str, image_prompt: str = "") -> str:
    # 1. Build a visual prompt
    llm = get_text_llm()
    prompt_builder_sys = (
        "You are an expert visual prompt engineer for diffusion models. "
        "Convert the text intent into a highly descriptive, comma-separated visual prompt.\n"
        "Format: [Main Subject], [Action/Setting], [Lighting/Atmosphere], [Art Style/Medium/Camera Angle].\n"
        "Keep it strictly under 50 words. CRITICAL: Output ONLY the prompt string. No markdown, no quotes, no introductory text."
    )
    
    extra_instructions = f"\nUser's Specific Image Instructions: {image_prompt.strip()}" if image_prompt and image_prompt.strip() else ""
    prompt_builder_human = f"Topic: {topic}\nTone: {tone}\nText Snippet: {generated_text[:200]}" + extra_instructions
    
    visual_prompt_res = llm.invoke([
        SystemMessage(content=prompt_builder_sys),
        HumanMessage(content=prompt_builder_human)
    ])
    visual_prompt = visual_prompt_res.content

    # 2. Call Image Model via OpenRouter
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "MAGNA AI Generator"
    }
    data = {
        "model": "black-forest-labs/flux.2-klein-4b",
        "messages": [
            {"role": "user", "content": f"Generate an image for this description: {visual_prompt}"}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60.0)
            response.raise_for_status()
            result = response.json()
            import json
            result_str = json.dumps(result)
            
            if "data:image" in result_str:
                start = result_str.find("data:image")
                end_quote = result_str.find('"', start)
                end_paren = result_str.find(')', start)
                
                ends = [e for e in [end_quote, end_paren] if e != -1]
                end = min(ends) if ends else len(result_str)
                
                url = result_str[start:end].replace('\\n', '').replace('\\r', '').replace('\\', '').replace(' ', '')
                return url
                
            url_match = re.search(r'(https?://[^\s"\'\)\\]+)', result_str)
            if url_match:
                return url_match.group(1).replace('\\/', '/')
                
            raise ValueError(f"No image URL found in response: {result}")
        except httpx.HTTPStatusError as e:
            print(f"Image generation failed: {e}")
            print(f"Error Details: {e.response.text}")
            raise # Re-raise for tenacity to catch and retry
        except Exception as e:
            print(f"Image generation failed: {e}")
            raise # Re-raise for tenacity to catch and retry
