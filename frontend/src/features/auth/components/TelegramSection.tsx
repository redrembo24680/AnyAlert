"use client";

import { useState } from "react";
import { generateLinkCode, unlinkTelegram } from "@/features/auth/api/telegram";
import type { UserReadResponse } from "@/shared/types/api";

interface TelegramSectionProps {
    user: UserReadResponse;
    onStatusChange: () => void; // called after link/unlink so parent can refresh
}

export function TelegramSection({ user, onStatusChange }: TelegramSectionProps) {
    const [linkCode, setLinkCode] = useState<string | null>(null);
    const [botUsername, setBotUsername] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState<{ text: string; type: "success" | "error" } | null>(null);

    const isLinked = !!user.telegram_id;

    async function handleGenerateCode() {
        setLoading(true);
        setMsg(null);
        try {
            const data = await generateLinkCode();
            setLinkCode(data.code);
            setBotUsername(data.bot_username);
        } catch (e) {
            setMsg({ text: "Не вдалося згенерувати код. Спробуйте ще раз.", type: "error" });
        } finally {
            setLoading(false);
        }
    }

    async function handleUnlink() {
        if (!confirm("Від'язати Telegram від вашого акаунту?")) return;
        setLoading(true);
        setMsg(null);
        try {
            await unlinkTelegram();
            setMsg({ text: "Telegram успішно від'язаний.", type: "success" });
            setLinkCode(null);
            onStatusChange();
        } catch (e) {
            setMsg({ text: "Не вдалося від'язати Telegram. Спробуйте ще раз.", type: "error" });
        } finally {
            setLoading(false);
        }
    }

    function handleCopy() {
        if (linkCode) navigator.clipboard.writeText(`/link ${linkCode}`);
    }

    return (
        <section className="glass-card telegram-section">
            <div className="card-header">
                <div className="icon-circle tg-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12L7.17 13.67l-2.95-.924c-.64-.203-.658-.64.136-.954l11.52-4.44c.534-.194 1.003.131.832.869z"/>
                    </svg>
                </div>
                <h2>Telegram</h2>
            </div>

            {isLinked ? (
                <div className="tg-linked-state">
                    <p className="tg-status linked">
                        ✅ Прив'язано
                        {user.telegram_username && (
                            <span className="tg-username"> @{user.telegram_username}</span>
                        )}
                    </p>
                    <p className="tg-hint">Ви отримуватимете сповіщення про трекери у Telegram-боті.</p>
                    <button
                        className="btn-danger-outline"
                        onClick={handleUnlink}
                        disabled={loading}
                    >
                        {loading ? "Зачекайте..." : "Від'язати Telegram"}
                    </button>
                </div>
            ) : (
                <div className="tg-unlinked-state">
                    <p className="tg-status unlinked">❌ Не прив'язаний</p>
                    <p className="tg-hint">
                        Прив'яжіть Telegram, щоб отримувати сповіщення про спрацювання трекерів прямо в месенджері.
                    </p>

                    {!linkCode ? (
                        <button
                            className="btn-tg"
                            onClick={handleGenerateCode}
                            disabled={loading}
                        >
                            {loading ? "Генеруємо..." : "Підключити Telegram"}
                        </button>
                    ) : (
                        <div className="tg-code-block">
                            <p className="tg-step">
                                <strong>Крок 1.</strong> Відкрийте{" "}
                                {botUsername ? (
                                    <a
                                        href={`https://t.me/${botUsername}?start=link_${linkCode}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="tg-bot-link"
                                    >
                                        @{botUsername}
                                    </a>
                                ) : (
                                    "бота AnyAlert"
                                )}{" "}
                                у Telegram.
                            </p>
                            <p className="tg-step">
                                <strong>Крок 2.</strong> Надішліть боту команду:
                            </p>
                            <div className="tg-code-row">
                                <code className="tg-code">/link {linkCode}</code>
                                <button
                                    className="btn-copy"
                                    onClick={handleCopy}
                                    title="Скопіювати"
                                >
                                    📋
                                </button>
                            </div>
                            <p className="tg-hint">Код дійсний 15 хвилин.</p>
                            <button
                                className="btn-outline-sm"
                                onClick={() => { setLinkCode(null); onStatusChange(); }}
                            >
                                Вже підключив — оновити статус
                            </button>
                        </div>
                    )}
                </div>
            )}

            {msg && (
                <div className={`status-message ${msg.type}`}>
                    {msg.type === "success" ? "✅ " : "❌ "}{msg.text}
                </div>
            )}
        </section>
    );
}
