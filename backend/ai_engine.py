import os
import re
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def get_text_llm():
    return ChatOpenAI(
        model="deepseek/deepseek-v4-flash",
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        base_url=OPENROUTER_BASE_URL,
        temperature=0.7,
    )

def generate_content(topic: str, tone: str, audience: str, content_type: str, description: str = "") -> str:
    llm = get_text_llm()
    
    extra_instructions = f"\nAdditional Instructions: {description}" if description else ""
    
    if content_type.lower() == "blog":
        system_prompt = "You are an expert blog writer. Write a comprehensive, engaging blog post."
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\nPlease write the blog post."
    elif content_type.lower() == "linkedin":
        system_prompt = "You are a LinkedIn influencer. Write a catchy, professional LinkedIn post with emojis and hashtags."
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\nPlease write the LinkedIn post."
    elif content_type.lower() == "twitter thread":
        system_prompt = "You are an expert social media manager. Write a highly engaging, viral Twitter thread. Use concise, punchy tweets, numbering (e.g., 1/x), and relevant hashtags."
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\nPlease write the Twitter thread."
    elif content_type.lower() == "instagram caption":
        system_prompt = "You are a social media influencer. Write a captivating Instagram caption that drives engagement. Include a strong hook, emojis, and relevant hashtags."
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\nPlease write the Instagram caption."
    elif content_type.lower() == "facebook post":
        system_prompt = "You are a community manager. Write an engaging and conversational Facebook post that encourages comments and shares."
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\nPlease write the Facebook post."
    elif content_type.lower() == "email newsletter":
        system_prompt = "You are an expert email marketer. Write a compelling email newsletter with a strong subject line, engaging body, and clear call-to-action."
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\nPlease write the email newsletter."
    elif content_type.lower() == "product description":
        system_prompt = "You are an e-commerce copywriter. Write a persuasive, SEO-friendly product description that highlights benefits and drives sales."
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\nPlease write the product description."
    elif content_type.lower() == "youtube script":
        system_prompt = "You are a YouTube content creator. Write a highly engaging video script including a hook, intro, main content body, and an outro with a call-to-action."
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\nPlease write the YouTube script."
    elif content_type.lower() == "ad copy":
        system_prompt = "You are a master copywriter. Write a high-converting, persuasive ad copy."
        human_prompt = "Topic: {topic}\nTone: {tone}\nTarget Audience: {audience}" + extra_instructions + "\nPlease write the ad copy."
    else:
        system_prompt = "You are a professional content creator."
        human_prompt = f"Create a {content_type} about {{topic}} with a {{tone}} tone for {{audience}}." + extra_instructions

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

def analyze_text(state: GraphState):
    llm = get_text_llm()
    prompt = f"Analyze the following text and identify areas for improvement based on this goal: '{state['goal']}'.\n\nText:\n{state['original_text']}"
    res = llm.invoke([HumanMessage(content=prompt)])
    return {"analysis": res.content}

def refine_text(state: GraphState):
    llm = get_text_llm()
    prompt = f"Original text: {state['original_text']}\n\nAnalysis: {state['analysis']}\n\nRewrite the text to achieve this goal: '{state['goal']}'. Return ONLY the rewritten text."
    res = llm.invoke([HumanMessage(content=prompt)])
    return {"refined_text": res.content}

def generate_explanation(state: GraphState):
    llm = get_text_llm()
    prompt = f"Original text: {state['original_text']}\nRefined text: {state['refined_text']}\n\nBriefly explain what was changed to achieve the goal: '{state['goal']}'. Keep it to 2-3 sentences."
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

async def generate_matching_image(topic: str, tone: str, generated_text: str, image_prompt: str = "") -> str:
    # 1. Build a visual prompt
    if image_prompt and image_prompt.strip():
        visual_prompt = image_prompt.strip()
    else:
        llm = get_text_llm()
        prompt_builder_sys = "You are a visual prompt engineer. Based on the topic, tone, and text, create a detailed, visual prompt for an image generation model. Keep it under 50 words. Do not include introductory text, just the prompt."
        prompt_builder_human = f"Topic: {topic}\nTone: {tone}\nText Snippet: {generated_text[:200]}"
        
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
        "X-Title": "Magna AI Suite"
    }
    data = {
        #"model": "bytedance-seed/seedream-4.5",
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
        except Exception as e:
            print(f"Image generation failed: {e}")
            
    return "https://via.placeholder.com/1024x1024.png?text=Image+Generation+Failed"
