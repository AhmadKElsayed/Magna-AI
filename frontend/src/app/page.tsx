"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from 'react-markdown';
import Link from 'next/link';
import Auth from '../components/Auth';
import { supabase } from '../lib/supabaseClient';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_URL = BASE_URL.endsWith('/api') ? BASE_URL : `${BASE_URL}/api`;

type Post = {
  id: string;
  session_id: string;
  topic: string;
  tone: string;
  audience: string;
  content_type: string;
  generated_text: string;
  image_url?: string;
  created_at: string;
};

type RefinedPost = {
  id: string;
  session_id: string;
  original_text: string;
  goal: string;
  refined_text: string;
  explanation: string;
  created_at: string;
};

export default function Home() {
  const [sessionId, setSessionId] = useState("");
  const [posts, setPosts] = useState<Post[]>([]);
  const [refinedPosts, setRefinedPosts] = useState<RefinedPost[]>([]);
  const [activeTab, setActiveTab] = useState("generate"); // 'generate' | 'improve'
  const [expandedPost, setExpandedPost] = useState<Post | null>(null);
  const [postToDelete, setPostToDelete] = useState<{ id: string, type: 'generate' | 'improve' } | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [showLoader, setShowLoader] = useState(true);

  // Generator State
  const [topic, setTopic] = useState("");
  const [description, setDescription] = useState("");
  const [tone, setTone] = useState("Professional");
  const [audience, setAudience] = useState("General Public");
  const [contentType, setContentType] = useState("Blog");
  const [customContentType, setCustomContentType] = useState("");
  const [imagePrompt, setImagePrompt] = useState("");
  const [generatingText, setGeneratingText] = useState(false);
  const [generatingImageFor, setGeneratingImageFor] = useState<string | null>(null);

  // Improver State
  const [improveText, setImproveText] = useState("");
  const [improveGoal, setImproveGoal] = useState("Make it shorter");
  const [improving, setImproving] = useState(false);
  const [improvedResult, setImprovedResult] = useState<{ text: string, explanation: string } | null>(null);

  const [user, setUser] = useState<any>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    // Check auth session
    const checkSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user) {
        setUser(session.user);
        await initApp(session.user.id);
      } else {
        setAuthChecked(true);
      }
    };
    checkSession();
  }, []);

  const initApp = async (uid: string) => {
    setSessionId(uid);
    
    const cachedPosts = sessionStorage.getItem("magna_cache_posts");
    const cachedRefined = sessionStorage.getItem("magna_cache_refined");
    
    if (cachedPosts && cachedRefined) {
      setPosts(JSON.parse(cachedPosts));
      setRefinedPosts(JSON.parse(cachedRefined));
      setLoadingHistory(false);
      setShowLoader(false);
      setAuthChecked(true);
      
      // Silent background update
      fetchHistory(uid);
      fetchRefinedHistory(uid);
      return;
    }

    setLoadingHistory(true);
    await Promise.all([
      fetchHistory(uid),
      fetchRefinedHistory(uid)
    ]);
    setLoadingHistory(false);
    setTimeout(() => setShowLoader(false), 600);
    setAuthChecked(true);
  };

  const handleAuthSuccess = async (loggedInUser: any) => {
    setUser(loggedInUser);
    
    // Check for anonymous migration
    const oldSid = localStorage.getItem("magna_session_id");
    if (oldSid) {
      try {
        await fetch(`${API_URL}/migrate-session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ old_session_id: oldSid, new_user_id: loggedInUser.id })
        });
        localStorage.removeItem("magna_session_id");
      } catch (e) {
        console.error("Migration failed", e);
      }
    }
    
    await initApp(loggedInUser.id);
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setPosts([]);
    setRefinedPosts([]);
    setSessionId("");
    sessionStorage.removeItem("magna_cache_posts");
    sessionStorage.removeItem("magna_cache_refined");
  };

  if (!authChecked) {
    return (
      <div className="loader-overlay">
        <img src="/MagnaAI.png" alt="Magna AI Logo" style={{ height: '100px', animation: 'pulse 2s infinite' }} />
        <h2 style={{ marginTop: '1.5rem', color: 'var(--text-primary)', fontWeight: 500 }}>Loading workspace...</h2>
      </div>
    );
  }

  if (!user) {
    return <Auth onAuthSuccess={handleAuthSuccess} />;
  }

  async function fetchHistory(sid: string) {
    try {
      const res = await fetch(`${API_URL}/history?session_id=${sid}`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setPosts(data);
        try {
          sessionStorage.setItem("magna_cache_posts", JSON.stringify(data));
        } catch (err) {
          console.warn("Storage quota exceeded, caching skipped for posts.");
        }
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function fetchRefinedHistory(sid: string) {
    try {
      const res = await fetch(`${API_URL}/history/refined?session_id=${sid}`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setRefinedPosts(data);
        try {
          sessionStorage.setItem("magna_cache_refined", JSON.stringify(data));
        } catch (err) {
          console.warn("Storage quota exceeded, caching skipped for refined posts.");
        }
      }
    } catch (e) {
      console.error(e);
    }
  }

  const handleGenerateText = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneratingText(true);
    try {
      await fetch(`${API_URL}/generate-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          tone,
          audience,
          content_type: contentType === 'Other' ? customContentType : contentType,
          description,
          session_id: sessionId
        })
      });
      await fetchHistory(sessionId);
    } catch (e) {
      console.error(e);
    }
    setGeneratingText(false);
  };

  const handleGenerateImage = async (post: Post) => {
    setGeneratingImageFor(post.id);
    try {
      await fetch(`${API_URL}/generate-image`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          post_id: post.id,
          text: post.generated_text,
          topic: post.topic,
          tone: post.tone,
          image_prompt: imagePrompt
        })
      });
      await fetchHistory(sessionId);
    } catch (e) {
      console.error(e);
    }
    setGeneratingImageFor(null);
  };

  const handleExportPDF = (post: Post) => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    printWindow.document.write(`
      <html>
        <head>
          <title>${post.topic} - Magna AI Suite</title>
          <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
          <style>
            body { font-family: system-ui, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 2rem; }
            h1 { color: #111; border-bottom: 2px solid #eaeaea; padding-bottom: 0.5rem; margin-bottom: 0.5rem; }
            .meta { color: #666; font-size: 0.9rem; margin-bottom: 2rem; }
            #content { margin-top: 1.5rem; font-size: 1.05rem; }
            #content h1, #content h2, #content h3 { color: #111; margin-top: 1.5rem; border: none; }
            img { max-width: 100%; height: auto; margin-bottom: 1.5rem; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
            @media print {
              body { padding: 0; }
              img { box-shadow: none; }
            }
          </style>
        </head>
        <body>
          <h1>${post.topic}</h1>
          <div class="meta">Type: ${post.content_type} | Tone: ${post.tone} | Audience: ${post.audience}</div>
          ${post.image_url ? `<img src="${post.image_url}" alt="Generated Image" />` : ''}
          <div id="content"></div>
          <script>
            window.onload = () => { 
              document.getElementById('content').innerHTML = marked.parse(decodeURIComponent("${encodeURIComponent(post.generated_text)}"));
              setTimeout(() => { window.print(); window.close(); }, 500);
            }
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  const handleDelete = async (postId: string) => {
    try {
      await fetch(`${API_URL}/history/${postId}?session_id=${sessionId}`, { method: "DELETE" });
      await fetchHistory(sessionId);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteRefined = async (postId: string) => {
    try {
      await fetch(`${API_URL}/history/refined/${postId}?session_id=${sessionId}`, { method: "DELETE" });
      await fetchRefinedHistory(sessionId);
    } catch (e) {
      console.error(e);
    }
  };

  const handleImprove = async (e: React.FormEvent) => {
    e.preventDefault();
    setImproving(true);
    try {
      const res = await fetch(`${API_URL}/improve-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: improveText, goal: improveGoal, session_id: sessionId })
      });
      const data = await res.json();
      setImprovedResult({ text: data.refined_text, explanation: data.explanation });
      await fetchRefinedHistory(sessionId);
    } catch (e) {
      console.error(e);
    }
    setImproving(false);
  };

  const confirmDeletePost = (id: string, type: 'generate' | 'improve') => setPostToDelete({ id, type });
  const cancelDelete = () => setPostToDelete(null);
  const executeDelete = async () => {
    if (!postToDelete) return;
    if (postToDelete.type === 'generate') {
      await handleDelete(postToDelete.id);
    } else {
      await handleDeleteRefined(postToDelete.id);
    }
    setPostToDelete(null);
  };

  return (
    <>
      {showLoader && (
        <div className={`loader-overlay ${!loadingHistory ? 'fade-out' : ''}`}>
          <img src="/MagnaAI.png" alt="Magna AI Logo" style={{ height: '100px', animation: 'pulse 2s infinite' }} />
          <h2 style={{ marginTop: '1.5rem', color: 'var(--text-primary)', fontWeight: 500 }}>Loading workspace...</h2>
        </div>
      )}

      <div className={`app-container ${!loadingHistory ? 'fade-in' : ''}`}>
        <div className="container">
          <header className="header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <img src="/MagnaAI.png" alt="Magna AI Logo" style={{ height: '40px' }} />
              <div>
                <h1 style={{ margin: 0, lineHeight: 1 }}>MAGNA AI Suite</h1>
                <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Content that converts, generated instantly.</p>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Link href="/settings" className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', padding: 0, textDecoration: 'none', borderRadius: '8px' }} title="Settings">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>
              </Link>
              <button onClick={handleSignOut} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', padding: 0, cursor: 'pointer', borderRadius: '8px' }} title="Sign Out">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
              </button>
            </div>
          </header>

          <div className="main-layout">
            <aside>
              <div className="panel">
                <div className="tabs">
                  <button className={`tab ${activeTab === 'generate' ? 'active' : ''}`} onClick={() => setActiveTab('generate')}>Generate AI Content</button>
                  <button className={`tab ${activeTab === 'improve' ? 'active' : ''}`} onClick={() => setActiveTab('improve')}>Content Improver</button>
                </div>

                {activeTab === 'generate' ? (
                  <form onSubmit={handleGenerateText}>
                    <div className="form-group">
                      <label>Content Type</label>
                      <select className="select" value={contentType} onChange={e => setContentType(e.target.value)}>
                        <option>Ad Copy</option>
                        <option>Blog</option>
                        <option>Email Newsletter</option>
                        <option>Facebook Post</option>
                        <option>Instagram Caption</option>
                        <option>Landing Page</option>
                        <option>LinkedIn</option>
                        <option>Product Description</option>
                        <option>Twitter Thread</option>
                        <option>YouTube Script</option>
                        <option>Other</option>
                      </select>
                    </div>
                    {contentType === 'Other' && (
                      <div className="form-group">
                        <label>Specify Content Type</label>
                        <input className="input" placeholder="e.g. Email Newsletter" value={customContentType} onChange={e => setCustomContentType(e.target.value)} required />
                      </div>
                    )}
                    <div className="form-group">
                      <label>Topic</label>
                      <input className="input" placeholder="e.g. AI in Healthcare" value={topic} onChange={e => setTopic(e.target.value)} required />
                    </div>
                    <div className="form-group">
                      <label>Tone</label>
                      <input className="input" placeholder="e.g. Professional, Witty" value={tone} onChange={e => setTone(e.target.value)} required />
                    </div>
                    <div className="form-group">
                      <label>Target Audience</label>
                      <input className="input" placeholder="e.g. Healthcare Professionals" value={audience} onChange={e => setAudience(e.target.value)} required />
                    </div>
                    <div className="form-group">
                      <label>Additional Description (Optional)</label>
                      <textarea className="textarea" style={{ minHeight: '80px' }} placeholder="Any specific requirements or instructions for the content..." value={description} onChange={e => setDescription(e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label>Custom Image Prompt (Optional)</label>
                      <textarea className="textarea" style={{ minHeight: '80px' }} placeholder="Specific instructions for the generated image..." value={imagePrompt} onChange={e => setImagePrompt(e.target.value)} />
                    </div>
                    <button type="submit" className="btn" disabled={generatingText}>
                      {generatingText && <span className="spinner"></span>}
                      Generate Content
                    </button>
                  </form>
                ) : (
                  <form onSubmit={handleImprove}>
                    <div className="form-group">
                      <label>Original Text</label>
                      <textarea className="textarea" placeholder="Paste text here..." value={improveText} onChange={e => setImproveText(e.target.value)} required />
                    </div>
                    <div className="form-group">
                      <label>Improvement Goal</label>
                      <input className="input" placeholder="e.g. Make it shorter, more formal" value={improveGoal} onChange={e => setImproveGoal(e.target.value)} required />
                    </div>
                    <button type="submit" className="btn" disabled={improving}>
                      {improving && <span className="spinner"></span>}
                      Improve Text
                    </button>
                  </form>
                )}

                {improvedResult && activeTab === 'improve' && (
                  <div style={{ marginTop: '1.5rem' }}>
                    <div className="explanation-box">
                      <strong>AI Explanation:</strong> {improvedResult.explanation}
                    </div>
                    <div className="result-box">
                      <ReactMarkdown>{improvedResult.text}</ReactMarkdown>
                    </div>
                    <button className="btn btn-secondary" onClick={() => navigator.clipboard.writeText(improvedResult.text)}>Copy Refined Text</button>
                  </div>
                )}
              </div>
            </aside>

            <main>
              <h2 className="panel-title">{activeTab === 'generate' ? "Content Dashboard" : "Refined Content Dashboard"}</h2>
              {activeTab === 'generate' ? (
                <div className="history-grid">
                  {posts.map(post => (
                    <div key={post.id} className="history-card" onClick={() => setExpandedPost(post)}>
                      {postToDelete?.id === post.id && postToDelete?.type === 'generate' && (
                        <div className="delete-overlay" onClick={e => e.stopPropagation()}>
                          <h4>Delete this generation?</h4>
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>This action cannot be undone.</p>
                          <div className="delete-actions">
                            <button className="btn btn-danger" onClick={executeDelete}>Yes, Delete</button>
                            <button className="btn btn-secondary" onClick={cancelDelete}>Cancel</button>
                          </div>
                        </div>
                      )}
                      {post.image_url ? (
                        <div style={{ position: 'relative' }}>
                          <img src={post.image_url} alt="Generated" className="history-img" />
                          <a href={post.image_url} download={`image-${post.id}.png`} className="btn btn-secondary" style={{ position: 'absolute', bottom: '10px', right: '10px', padding: '0.4rem 0.8rem', fontSize: '0.8rem', width: 'auto' }}>Download</a>
                        </div>
                      ) : (
                        <div className="history-img" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#52525b' }}>
                          No Image Generated
                        </div>
                      )}
                      <div className="history-content">
                        <div className="history-meta">
                          <span className="badge">{post.content_type}</span>
                          <span className="badge">{post.tone}</span>
                          <span className="badge">Audience: {post.audience}</span>
                        </div>
                        <div className="history-text"><ReactMarkdown>{post.generated_text}</ReactMarkdown></div>
                      </div>
                      <div className="history-actions" onClick={e => e.stopPropagation()}>
                        <button className="btn btn-secondary" onClick={() => navigator.clipboard.writeText(post.generated_text)}>Copy Text</button>
                        <button className="btn btn-secondary" disabled={generatingImageFor === post.id} onClick={() => handleGenerateImage(post)}>
                          {generatingImageFor === post.id ? "Generating..." : (post.image_url ? "Regenerate Image" : "Generate Image")}
                        </button>
                        <button className="btn btn-secondary" onClick={() => handleExportPDF(post)}>Export PDF</button>
                        <button className="btn btn-danger" onClick={() => confirmDeletePost(post.id, 'generate')}>Delete</button>
                      </div>
                    </div>
                  ))}
                  {posts.length === 0 && <p style={{ color: 'var(--text-secondary)', marginTop: '2rem' }}>No generated content yet. Start creating!</p>}
                </div>
              ) : (
                <div className="history-grid">
                  {refinedPosts.map(post => (
                    <div key={post.id} className="history-card">
                      {postToDelete?.id === post.id && postToDelete?.type === 'improve' && (
                        <div className="delete-overlay" onClick={e => e.stopPropagation()}>
                          <h4>Delete this refined text?</h4>
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>This action cannot be undone.</p>
                          <div className="delete-actions">
                            <button className="btn btn-danger" onClick={executeDelete}>Yes, Delete</button>
                            <button className="btn btn-secondary" onClick={cancelDelete}>Cancel</button>
                          </div>
                        </div>
                      )}
                      <div className="history-content" style={{ padding: '1.5rem', maxHeight: 'none' }}>
                        <div className="explanation-box" style={{ marginBottom: '1rem' }}>
                          <strong>Goal:</strong> {post.goal} <br />
                          <strong>Explanation:</strong> {post.explanation}
                        </div>
                        <div className="history-text" style={{ maxHeight: '250px' }}><ReactMarkdown>{post.refined_text}</ReactMarkdown></div>
                      </div>
                      <div className="history-actions" onClick={e => e.stopPropagation()}>
                        <button className="btn btn-secondary" onClick={() => navigator.clipboard.writeText(post.refined_text)}>Copy Refined Text</button>
                        <button className="btn btn-danger" onClick={() => confirmDeletePost(post.id, 'improve')}>Delete</button>
                      </div>
                    </div>
                  ))}
                  {refinedPosts.length === 0 && <p style={{ color: 'var(--text-secondary)', marginTop: '2rem' }}>No refined content yet. Start improving!</p>}
                </div>
              )}
            </main>
          </div>

        </div>
      </div>
      
      {expandedPost && (
        <div className="modal-overlay" onClick={() => setExpandedPost(null)}>
          <button className="modal-close" onClick={() => setExpandedPost(null)}>&times;</button>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            {expandedPost.image_url && (
              <div style={{ position: 'relative' }}>
                <img src={expandedPost.image_url} alt="Generated" style={{ width: '100%', height: 'auto', maxHeight: '500px', objectFit: 'cover', background: '#000' }} />
                <a href={expandedPost.image_url} download={`image-${expandedPost.id}.png`} className="btn btn-secondary" style={{ position: 'absolute', bottom: '15px', right: '15px', padding: '0.5rem 1rem', width: 'auto', background: 'rgba(18, 18, 20, 0.8)', backdropFilter: 'blur(4px)' }}>Download Image</a>
              </div>
            )}
            <div style={{ padding: '2rem' }}>
              <div className="history-meta" style={{ marginBottom: '1rem' }}>
                <span className="badge">{expandedPost.content_type}</span>
                <span className="badge">{expandedPost.tone}</span>
                <span className="badge">Audience: {expandedPost.audience}</span>
              </div>
              <div className="history-text" style={{ fontSize: '1.05rem', maxHeight: 'none', lineHeight: '1.7' }}>
                <ReactMarkdown>{expandedPost.generated_text}</ReactMarkdown>
              </div>
              <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', borderTop: '1px solid var(--border)', paddingTop: '1.5rem' }}>
                <button className="btn btn-secondary" onClick={() => handleExportPDF(expandedPost)}>Export to PDF</button>
                <button className="btn btn-secondary" onClick={() => navigator.clipboard.writeText(expandedPost.generated_text)}>Copy Text</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
