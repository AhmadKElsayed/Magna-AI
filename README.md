# Magna AI Suite

Magna AI Suite is a powerful, full-stack web application designed for marketing and social media professionals. It allows you to generate highly customized, engaging content for a variety of platforms (Twitter, LinkedIn, YouTube, Instagram, etc.) and uses advanced AI to synthesize matching visual assets.

![Magna AI Suite](frontend/public/MagnaAI.png)

## Features

- **Multi-Platform Content Generation**: Create tailored content for Blogs, LinkedIn, Twitter Threads, Instagram Captions, Facebook Posts, Email Newsletters, Product Descriptions, YouTube Scripts, and Ad Copy.
- **Custom Visual Prompts & Image Synthesis**: Generate matching images via OpenRouter's `flux.2-klein-4b` model, using either auto-generated visual prompts or entirely custom user instructions.
- **Content Improver (LangGraph Workflow)**: A sophisticated multi-step AI agent workflow that analyzes your draft against a specific goal (e.g., "Make it punchier") and automatically refines it, providing an explanation of what was changed.
- **Persistent History Dashboards**: Full integration with Supabase saves both generated and refined content into persistent, easy-to-use history dashboards.
- **Native PDF Export**: Cleanly convert generated markdown posts and their associated images directly into beautifully formatted, printable PDFs using zero dependencies.

## Tech Stack

### Frontend
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Vanilla CSS (`globals.css`)
- **Key Libraries**: `react-markdown`

### Backend
- **Framework**: FastAPI
- **Language**: Python
- **AI Models**:
  - `deepseek/deepseek-v4-flash` (Text Generation via OpenRouter)
  - `black-forest-labs/flux.2-klein-4b` (Image Generation via OpenRouter)
- **AI Tooling**: LangChain, LangGraph
- **Database**: Supabase (PostgreSQL)

## Getting Started

### Prerequisites
- [Node.js](https://nodejs.org/)
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- OpenRouter API Key
- Supabase Project & API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AhmadKElsayed/Magna-AI.git
   cd Magna-AI
   ```

2. **Backend Setup**
   Ensure `uv` is installed. Create a `.env` file in the `backend` directory:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   ```

3. **Frontend Setup**
   Navigate to the `frontend` directory and install dependencies:
   ```bash
   cd frontend
   npm install
   ```
   Create a `.env.local` file in the `frontend` directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Database Setup**
   Run the following SQL queries in your Supabase SQL Editor:
   ```sql
   CREATE TABLE IF NOT EXISTS posts (
     id uuid PRIMARY KEY,
     session_id text NOT NULL,
     topic text NOT NULL,
     tone text NOT NULL,
     audience text NOT NULL,
     content_type text NOT NULL,
     generated_text text NOT NULL,
     image_url text,
     description text,
     image_prompt text,
     created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
   );

   CREATE TABLE IF NOT EXISTS refined_posts (
     id uuid PRIMARY KEY,
     session_id text NOT NULL,
     original_text text NOT NULL,
     goal text NOT NULL,
     refined_text text NOT NULL,
     explanation text NOT NULL,
     created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
   );
   ```

### Running the Application

You can spin up both the Next.js frontend and the FastAPI backend simultaneously using the provided unified runner:

```bash
uv run main.py
```

The frontend will be available at `http://localhost:3000` and the API at `http://localhost:8000`.

## License
MIT License
