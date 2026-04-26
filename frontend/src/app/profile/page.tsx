"use client";

import { useEffect, useState, FormEvent } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { getMe, updateMe } from "@/features/profile/api/user";
import { getMyTrackers, deleteTracker } from "@/features/tracking/api/trackers";
import type { UserReadResponse, TrackerResponse } from "@/shared/types/api";
import Link from "next/link";

export default function ProfilePage() {
    const { isAuthenticated, login } = useAuth();
    const [userData, setUserData] = useState<UserReadResponse | null>(null);
    const [trackers, setTrackers] = useState<TrackerResponse[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

    // Form states
    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");

    useEffect(() => {
        if (!isAuthenticated) return;

        async function fetchData() {
            const session = localStorage.getItem("anyalert:session");
            if (!session) return;
            const { token } = JSON.parse(session);

            try {
                const [user, trackersList] = await Promise.all([
                    getMe(token),
                    getMyTrackers(token)
                ]);
                setUserData(user);
                setTrackers(trackersList);
                setFullName(user.full_name || "");
                setEmail(user.email);
            } catch (error) {
                console.error("Failed to fetch profile data:", error);
            } finally {
                setIsLoading(false);
            }
        }

        fetchData();
    }, [isAuthenticated]);

    async function handleUpdateProfile(e: FormEvent) {
        e.preventDefault();
        setMessage(null);
        setIsSaving(true);

        const session = localStorage.getItem("anyalert:session");
        if (!session) return;
        const authData = JSON.parse(session);

        try {
            const updatedUser = await updateMe({ full_name: fullName, email }, authData.token);
            setUserData(updatedUser);
            
            // Update auth context/localstorage
            login({
                ...authData,
                user: {
                    name: updatedUser.full_name || "",
                    email: updatedUser.email
                }
            });
            
            setMessage({ text: "Профіль успішно оновлено", type: "success" });
        } catch (error: any) {
            setMessage({ text: "Не вдалося оновити профіль. Можливо, такий email вже зайнятий.", type: "error" });
        } finally {
            setIsSaving(false);
        }
    }

    async function handleDeleteTracker(trackerId: number) {
        if (!confirm("Ви впевнені, що хочете видалити це відстеження?")) return;

        const session = localStorage.getItem("anyalert:session");
        if (!session) return;
        const { token } = JSON.parse(session);

        try {
            await deleteTracker(trackerId, token);
            setTrackers(current => current.filter(t => t.id !== trackerId));
        } catch (error) {
            console.error("Failed to delete tracker:", error);
            alert("Не вдалося видалити відстеження.");
        }
    }

    if (!isAuthenticated) {
        return (
            <div className="profile-container">
                <div className="profile-card">
                    <h2>Доступ обмежено</h2>
                    <p>Будь ласка, увійдіть в акаунт, щоб переглянути свій профіль.</p>
                    <Link href="/login" className="btn-primary">Увійти</Link>
                </div>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="profile-loading-wrap">
                <span className="loader-large"></span>
                <p>Завантажуємо ваш профіль...</p>
            </div>
        );
    }

    return (
        <div className="profile-wrapper">
            <header className="profile-header">
                <h1 className="gradient-text">Мій Профіль</h1>
                <p className="profile-subtitle">Керуйте своїми даними та відстеженнями в одному місці</p>
            </header>

            <div className="profile-grid">
                {/* Left Column: Personal Info */}
                <div className="profile-aside">
                    <section className="glass-card profile-info-card">
                        <div className="card-header">
                            <div className="icon-circle user-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                            </div>
                            <h2>Налаштування акаунта</h2>
                        </div>
                        
                        <form onSubmit={handleUpdateProfile} className="profile-form">
                            <div className="input-group">
                                <label htmlFor="fullName">Ваше ім'я</label>
                                <input
                                    id="fullName"
                                    type="text"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    placeholder="Наприклад: Олександр"
                                />
                            </div>
                            <div className="input-group">
                                <label htmlFor="email">Електронна пошта</label>
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="you@example.com"
                                />
                            </div>
                            <button type="submit" className="save-button" disabled={isSaving}>
                                {isSaving ? (
                                    <span className="loader-small"></span>
                                ) : (
                                    "Оновити профіль"
                                )}
                            </button>
                            {message && (
                                <div className={`status-message ${message.type}`}>
                                    {message.type === 'success' ? '✅ ' : '❌ '} {message.text}
                                </div>
                            )}
                        </form>
                    </section>

                    <div className="glass-card stats-card">
                        <div className="stat-item">
                            <span className="stat-label">Всього тригерів</span>
                            <span className="stat-value">{trackers.length}</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-label">Активних</span>
                            <span className="stat-value active">{trackers.filter(t => t.is_active).length}</span>
                        </div>
                    </div>
                </div>

                {/* Right Column: Trackers List */}
                <div className="profile-main">
                    <section className="trackers-container">
                        <div className="section-header">
                            <h2>Мої відстеження</h2>
                        </div>

                        {trackers.length === 0 ? (
                            <div className="glass-card empty-state">
                                <div className="empty-icon">🔔</div>
                                <h3>У вас ще немає тригерів</h3>
                                <p>Оберіть платформу та додайте свій перший товар для моніторингу цін.</p>
                                <Link href="/platforms" className="cta-button">Перейти до платформ</Link>
                            </div>
                        ) : (
                            <div className="trackers-grid">
                                {trackers.map((tracker) => (
                                    <div key={tracker.id} className={`tracker-card ${!tracker.is_active ? 'finished' : ''}`}>
                                        <div className="tracker-top">
                                            <span className="network-tag">{tracker.network}</span>
                                            <div className="tracker-actions-top">
                                                <span className={`status-dot ${tracker.is_active ? 'pulse' : ''}`}></span>
                                                <button 
                                                    className="delete-icon-btn" 
                                                    onClick={() => handleDeleteTracker(tracker.id)}
                                                    title="Видалити"
                                                >
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                                                </button>
                                            </div>
                                        </div>
                                        <div className="tracker-content">
                                            <h3 title={tracker.title || ""}>
                                                {tracker.title || "Завантаження інформації..."}
                                            </h3>
                                            <a href={tracker.url} target="_blank" rel="noopener noreferrer" className="url-link">
                                                {new URL(tracker.url).hostname}
                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                                            </a>
                                        </div>
                                        <div className="tracker-footer">
                                            <div className="trigger-info">
                                                <span className="trigger-type">
                                                    {tracker.trigger_type === 'price_drop' ? '📉 Ціна нижче' : 
                                                     tracker.trigger_type === 'in_stock' ? '📦 Наявність' : '🔔 Зміни'}
                                                </span>
                                                {tracker.trigger_value && (
                                                    <span className="trigger-val">{tracker.trigger_value} грн</span>
                                                )}
                                            </div>
                                            {tracker.last_price && (
                                                <div className="last-price">
                                                    {tracker.last_price} грн
                                                </div>
                                            )}
                                        </div>
                                        {!tracker.is_active && (
                                            <div className="finished-overlay">
                                                <span>Тригер спрацював</span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>
                </div>
            </div>

            <style jsx>{`
                .profile-wrapper {
                    max-width: 1120px;
                    margin: 0 auto;
                    animation: fadeIn 0.5s ease-out;
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .profile-header {
                    margin-bottom: 4rem;
                    text-align: center;
                }
                .gradient-text {
                    font-size: 3.5rem;
                    font-weight: 900;
                    margin: 0;
                    background: linear-gradient(135deg, #26180c 0%, #cf5f28 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    text-align: center;
                }
                .profile-subtitle {
                    color: #6b5a4b;
                    font-size: 1.1rem;
                    margin-top: 0.5rem;
                }
                .profile-grid {
                    display: grid;
                    grid-template-columns: 320px 1fr;
                    gap: 3rem;
                    align-items: start;
                }
                @media (max-width: 1024px) {
                    .profile-grid { grid-template-columns: 1fr; }
                }
                .glass-card {
                    background: white;
                    border: 1px solid #e9d3b4;
                    border-radius: 24px;
                    padding: 2rem;
                    box-shadow: 0 10px 30px rgba(107, 90, 75, 0.05);
                }
                .card-header {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    margin-bottom: 2rem;
                }
                .icon-circle {
                    width: 40px;
                    height: 40px;
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: #cf5f28;
                    color: white;
                }
                h2 {
                    font-size: 1.25rem;
                    margin: 0;
                    font-weight: 700;
                    color: #26180c;
                }
                .input-group {
                    margin-bottom: 1.5rem;
                }
                label {
                    display: block;
                    font-size: 0.85rem;
                    font-weight: 700;
                    color: #6b5a4b;
                    margin-bottom: 0.5rem;
                }
                input {
                    width: 100%;
                    padding: 0.8rem 1rem;
                    border-radius: 14px;
                    border: 1.5px solid #e9d3b4;
                    background: #fff;
                    font-size: 1rem;
                    transition: all 0.2s;
                }
                input:focus {
                    border-color: #cf5f28;
                    outline: none;
                }
                .save-button {
                    width: 100%;
                    padding: 1rem;
                    border-radius: 14px;
                    border: none;
                    background: #cf5f28;
                    color: white;
                    font-weight: 700;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .save-button:hover {
                    background: #a94719;
                    transform: translateY(-2px);
                }
                .status-message {
                    margin-top: 1rem;
                    padding: 0.8rem;
                    border-radius: 10px;
                    font-size: 0.85rem;
                    font-weight: 600;
                    text-align: center;
                }
                .status-message.success { background: #ecfdf5; color: #065f46; }
                .status-message.error { background: #fef2f2; color: #991b1b; }

                .stats-card {
                    margin-top: 1.5rem;
                    display: flex;
                    justify-content: space-around;
                    padding: 1.5rem;
                }
                .stat-item {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }
                .stat-label { font-size: 0.75rem; color: #6b5a4b; font-weight: 600; }
                .stat-value { font-size: 1.8rem; font-weight: 800; color: #26180c; }
                .stat-value.active { color: #cf5f28; }

                .section-header {
                    margin-bottom: 2rem;
                }

                .trackers-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                    gap: 1.5rem;
                }
                .tracker-card {
                    background: white;
                    border: 1px solid #e9d3b4;
                    border-radius: 20px;
                    padding: 1.5rem;
                    position: relative;
                    overflow: hidden;
                    transition: all 0.3s;
                }
                .tracker-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 12px 24px rgba(0,0,0,0.05);
                    border-color: #cf5f28;
                }
                .tracker-top {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                }
                .network-tag {
                    font-size: 0.65rem;
                    font-weight: 800;
                    text-transform: uppercase;
                    background: #f4efe6;
                    color: #6b5a4b;
                    padding: 0.3rem 0.7rem;
                    border-radius: 6px;
                }
                .tracker-actions-top {
                    display: flex;
                    align-items: center;
                    gap: 0.8rem;
                }
                .status-dot {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #cf5f28;
                }
                .status-dot.pulse {
                    box-shadow: 0 0 0 0 rgba(207, 95, 40, 0.7);
                    animation: pulse 2s infinite;
                }
                @keyframes pulse {
                    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(207, 95, 40, 0.7); }
                    70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(207, 95, 40, 0); }
                    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(207, 95, 40, 0); }
                }
                .delete-icon-btn {
                    background: none;
                    border: none;
                    color: #aaa;
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 6px;
                    transition: all 0.2s;
                    display: flex;
                }
                .delete-icon-btn:hover {
                    color: #ef4444;
                    background: #fef2f2;
                }
                .tracker-content h3 {
                    font-size: 1.1rem;
                    margin: 0 0 0.5rem;
                    color: #26180c;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                    min-height: 2.8rem;
                }
                .url-link {
                    font-size: 0.8rem;
                    color: #6b5a4b;
                    display: flex;
                    align-items: center;
                    gap: 0.4rem;
                }
                .url-link:hover { color: #cf5f28; }
                .tracker-footer {
                    margin-top: 1.5rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding-top: 1rem;
                    border-top: 1px dashed #e9d3b4;
                }
                .trigger-info { display: flex; flex-direction: column; }
                .trigger-type { font-size: 0.75rem; font-weight: 700; color: #6b5a4b; }
                .trigger-val { font-size: 0.95rem; font-weight: 800; color: #26180c; }
                .last-price {
                    font-size: 1.1rem;
                    font-weight: 900;
                    color: #cf5f28;
                }
                .finished { opacity: 0.6; }
                .finished-overlay {
                    position: absolute;
                    inset: 0;
                    background: rgba(255, 255, 255, 0.4);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    backdrop-filter: blur(1px);
                    pointer-events: none;
                }
                .finished-overlay span {
                    background: #26180c;
                    color: white;
                    padding: 0.4rem 1rem;
                    border-radius: 99px;
                    font-size: 0.75rem;
                    font-weight: 700;
                }
                .profile-loading-wrap {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 400px;
                    color: #6b5a4b;
                }
                .loader-large {
                    width: 48px;
                    height: 48px;
                    border: 4px solid #e9d3b4;
                    border-bottom-color: #cf5f28;
                    border-radius: 50%;
                    display: inline-block;
                    animation: rotation 1s linear infinite;
                    margin-bottom: 1rem;
                }
                .loader-small {
                    width: 18px;
                    height: 18px;
                    border: 2px solid white;
                    border-bottom-color: transparent;
                    border-radius: 50%;
                    display: inline-block;
                    animation: rotation 1s linear infinite;
                }
                @keyframes rotation {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .empty-state {
                    text-align: center;
                    padding: 4rem 2rem;
                }
            `}</style>
        </div>
    );
}

