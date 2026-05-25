"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { supabase } from '../../lib/supabaseClient';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_URL = BASE_URL.endsWith('/api') ? BASE_URL : `${BASE_URL}/api`;

export default function SettingsPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [coreValues, setCoreValues] = useState("");
  const [targetDemographic, setTargetDemographic] = useState("");
  const [wordsToAvoid, setWordsToAvoid] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  const [deletingAccount, setDeletingAccount] = useState(false);

  useEffect(() => {
    const initSettings = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      let sid = session?.user?.id;
      
      if (!sid) {
        sid = localStorage.getItem("magna_session_id") || "";
        if (!sid) {
          sid = Math.random().toString(36).substring(2, 15);
          localStorage.setItem("magna_session_id", sid);
        }
      }
      setSessionId(sid);
      
      try {
        const res = await fetch(`${API_URL}/settings?session_id=${sid}`);
        const data = await res.json();
        if (data && !data.error) {
          setCompanyName(data.company_name || "");
          setCoreValues(data.core_values || "");
          setTargetDemographic(data.target_demographic || "");
          setWordsToAvoid(data.words_to_avoid || "");
        }
      } catch (err) {
        console.error("Error fetching settings:", err);
      } finally {
        setLoading(false);
      }
    };
    initSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await fetch(`${API_URL}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          company_name: companyName,
          core_values: coreValues,
          target_demographic: targetDemographic,
          words_to_avoid: wordsToAvoid
        })
      });
      router.push('/');
    } catch (err) {
      console.error("Error saving settings:", err);
    }
    setSaving(false);
  };

  const handleReset = async () => {
    if (!confirm("Are you sure you want to clear your global brand profile?")) return;
    setSaving(true);
    try {
      await fetch(`${API_URL}/settings?session_id=${sessionId}`, { method: "DELETE" });
      setCompanyName("");
      setCoreValues("");
      setTargetDemographic("");
      setWordsToAvoid("");
    } catch (err) {
      console.error("Error deleting settings:", err);
    }
    setSaving(false);
  };

  const handleDeleteAccount = async () => {
    if (!confirm("CRITICAL WARNING: This will permanently delete your account and ALL your generated posts, refined texts, and brand profiles. This action CANNOT be undone. Are you absolutely sure?")) return;
    
    setDeletingAccount(true);
    try {
      await fetch(`${API_URL}/delete-account?session_id=${sessionId}`, { method: "DELETE" });
      await supabase.auth.signOut();
      localStorage.removeItem("magna_session_id");
      router.push('/');
    } catch (err) {
      console.error("Error deleting account:", err);
      alert("Failed to delete account. Please try again later.");
    }
    setDeletingAccount(false);
  };

  return (
    <div className="app-container fade-in">
      <div className="container" style={{ maxWidth: '800px' }}>
        <header className="header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
             <Link href="/" style={{ color: 'var(--text-secondary)', textDecoration: 'none', display: 'flex', alignItems: 'center', fontWeight: 'bold' }}>
               <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '0.5rem' }}><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
               Back
             </Link>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Brand Voice Settings</h1>
        </header>

        <main className="panel">
          <h2 className="panel-title" style={{ marginBottom: '1.5rem' }}>Global Brand Profile</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.9rem' }}>
            Define your core brand identity below. These settings will be automatically injected into every content generation to ensure a consistent voice.
          </p>
          
          {loading ? (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <span className="spinner" style={{ display: 'inline-block', borderLeftColor: 'var(--accent)', width: '24px', height: '24px' }}></span>
              <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>Loading profile...</p>
            </div>
          ) : (
            <form onSubmit={handleSave}>
              <div className="form-group">
                <label>Company / Brand Name</label>
                <input className="input" placeholder="e.g. Magna AI" value={companyName} onChange={e => setCompanyName(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Core Values & Personality</label>
                <textarea className="textarea" placeholder="e.g. We are innovative, professional, yet approachable and helpful." value={coreValues} onChange={e => setCoreValues(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Target Demographic Context</label>
                <textarea className="textarea" placeholder="e.g. Tech-savvy founders, small business owners looking to scale." value={targetDemographic} onChange={e => setTargetDemographic(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Words & Phrases to Strictly Avoid</label>
                <textarea className="textarea" placeholder="e.g. 'game-changer', 'revolutionary', excessive jargon." value={wordsToAvoid} onChange={e => setWordsToAvoid(e.target.value)} />
              </div>
              
              <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                <button type="submit" className="btn" disabled={saving} style={{ width: 'auto' }}>
                  {saving && <span className="spinner"></span>}
                  Save Global Profile
                </button>
                <button type="button" className="btn btn-danger" disabled={saving} onClick={handleReset} style={{ width: 'auto' }}>
                  Reset Profile
                </button>
                <Link href="/" className="btn btn-secondary" style={{ textAlign: 'center', textDecoration: 'none', width: 'auto' }}>Cancel</Link>
              </div>
            </form>
          )}
        </main>
        
        {!loading && (
          <main className="panel" style={{ marginTop: '2rem', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
            <h2 className="panel-title" style={{ color: '#ef4444', marginBottom: '1rem' }}>Danger Zone</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
              Permanently delete your account and all associated data (posts, images, brand profiles). This action is irreversible.
            </p>
            <button 
              type="button" 
              className="btn btn-danger" 
              disabled={deletingAccount} 
              onClick={handleDeleteAccount} 
              style={{ width: 'auto' }}
            >
              {deletingAccount ? 'Deleting...' : 'Delete Account'}
            </button>
          </main>
        )}

      </div>
    </div>
  );
}
