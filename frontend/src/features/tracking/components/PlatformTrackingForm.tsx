"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { createTracker } from "@/features/tracking/api/trackers";

import type { MarketplacePlatform } from "@/features/tracking/data/platforms";

type TriggerType =
    | "price_below"
    | "price_drop"
    | "price_rise"
    | "discount"
    | "rating_drop"
    | "views_reach"
    | "reviews_reach"
    | "in_stock"
    | "back_in_stock"
    | "trade_in_available"
    | "credit_available"
    | "delivery_available"
    | "pickup_available"
    | "personal_price_available"
    | "gift_offer_available"
    | "color_change"
    | "memory_variant_change"
    | "cashback_reach"
    | "any_change";

interface TriggerOption {
    type: TriggerType;
    title: string;
    inputLabel: string | null;
    placeholder: string;
    unitLabel?: string;
}

interface PlatformTrackingFormProps {
    platform: MarketplacePlatform;
}

const triggerOptionsByType: Record<TriggerType, TriggerOption> = {
    price_below: {
        type: "price_below",
        title: "Ціна опустилась нижче порогу",
        inputLabel: "Ціна нижче",
        placeholder: "Наприклад: 15999",
        unitLabel: "грн"
    },
    price_drop: {
        type: "price_drop",
        title: "Ціна знизилась до порогу",
        inputLabel: "Поріг ціни",
        placeholder: "Наприклад: 15000",
        unitLabel: "грн"
    },
    price_rise: {
        type: "price_rise",
        title: "Ціна виросла вище порогу",
        inputLabel: "Ціна вище",
        placeholder: "Наприклад: 20000",
        unitLabel: "грн"
    },
    discount: {
        type: "discount",
        title: "Знижка стала більшою",
        inputLabel: "Мінімальна знижка",
        placeholder: "Наприклад: 15",
        unitLabel: "%"
    },
    rating_drop: {
        type: "rating_drop",
        title: "Рейтинг впав нижче порогу",
        inputLabel: "Мінімальний рейтинг",
        placeholder: "Наприклад: 4.5"
    },
    views_reach: {
        type: "views_reach",
        title: "Кількість переглядів досягла значення",
        inputLabel: "Переглядів від",
        placeholder: "Наприклад: 500",
        unitLabel: "переглядів"
    },
    reviews_reach: {
        type: "reviews_reach",
        title: "Кількість відгуків досягла значення",
        inputLabel: "Відгуків від",
        placeholder: "Наприклад: 20",
        unitLabel: "відгуків"
    },
    in_stock: {
        type: "in_stock",
        title: "Товар з'явився у наявності",
        inputLabel: null,
        placeholder: ""
    },
    back_in_stock: {
        type: "back_in_stock",
        title: "Товар повернувся у наявність",
        inputLabel: null,
        placeholder: ""
    },
    trade_in_available: {
        type: "trade_in_available",
        title: "З'явився Trade-in",
        inputLabel: null,
        placeholder: ""
    },
    credit_available: {
        type: "credit_available",
        title: "З'явився кредит",
        inputLabel: null,
        placeholder: ""
    },
    delivery_available: {
        type: "delivery_available",
        title: "З'явилась доставка",
        inputLabel: null,
        placeholder: ""
    },
    pickup_available: {
        type: "pickup_available",
        title: "З'явився самовивіз",
        inputLabel: null,
        placeholder: ""
    },
    personal_price_available: {
        type: "personal_price_available",
        title: "З'явилась персональна ціна",
        inputLabel: null,
        placeholder: ""
    },
    gift_offer_available: {
        type: "gift_offer_available",
        title: "З'явився подарунок до товару",
        inputLabel: null,
        placeholder: ""
    },
    color_change: {
        type: "color_change",
        title: "Змінився колір товару",
        inputLabel: null,
        placeholder: ""
    },
    memory_variant_change: {
        type: "memory_variant_change",
        title: "Змінився варіант пам'яті",
        inputLabel: null,
        placeholder: ""
    },
    cashback_reach: {
        type: "cashback_reach",
        title: "Кешбек досяг порогу",
        inputLabel: "Кешбек від",
        placeholder: "Наприклад: 200",
        unitLabel: "грн"
    },
    any_change: {
        type: "any_change",
        title: "Будь-яка зміна товару",
        inputLabel: null,
        placeholder: ""
    }
};

const triggersByPlatform: Record<string, TriggerType[]> = {
    rozetka: ["price_below", "price_rise", "discount", "rating_drop", "back_in_stock", "any_change"],
    olx: ["price_below", "price_rise", "views_reach", "rating_drop", "back_in_stock", "any_change"],
    prom: ["price_below", "price_rise", "discount", "views_reach", "back_in_stock", "any_change"],
    allo: [
        "price_below",
        "price_rise",
        "discount",
        "cashback_reach",
        "reviews_reach",
        "trade_in_available",
        "credit_available",
        "color_change",
        "memory_variant_change",
        "back_in_stock",
        "any_change"
    ],
    comfy: ["price_below", "price_rise", "discount", "delivery_available", "pickup_available", "personal_price_available", "back_in_stock", "any_change"],
    foxtrot: ["price_below", "price_rise", "discount", "cashback_reach", "credit_available", "trade_in_available", "delivery_available", "pickup_available", "gift_offer_available", "back_in_stock", "any_change"]
};

const defaultTriggerValues: Record<TriggerType, string> = {
    price_below: "",
    price_drop: "",
    price_rise: "",
    discount: "",
    rating_drop: "",
    views_reach: "",
    reviews_reach: "",
    in_stock: "",
    back_in_stock: "",
    trade_in_available: "",
    credit_available: "",
    delivery_available: "",
    pickup_available: "",
    personal_price_available: "",
    gift_offer_available: "",
    color_change: "",
    memory_variant_change: "",
    cashback_reach: "",
    any_change: ""
};

export function PlatformTrackingForm({ platform }: PlatformTrackingFormProps) {
    const [productUrl, setProductUrl] = useState("");
    const triggerOptions = useMemo(() => {
        const triggerTypes = triggersByPlatform[platform.slug] ?? ["price_below", "back_in_stock"];
        return triggerTypes.map((type) => triggerOptionsByType[type]);
    }, [platform.slug]);

    const [selectedTriggers, setSelectedTriggers] = useState<TriggerType[]>([]);
    const [triggerValues, setTriggerValues] = useState<Record<TriggerType, string>>(defaultTriggerValues);
    const { isAuthenticated } = useAuth();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    useEffect(() => {
        const defaultType = triggerOptions[0]?.type;
        setSelectedTriggers(defaultType ? [defaultType] : []);
    }, [triggerOptions]);

    function toggleTrigger(triggerType: TriggerType) {
        setSelectedTriggers((current) => {
            if (current.includes(triggerType)) {
                return current.filter((item) => item !== triggerType);
            }

            return [...current, triggerType];
        });
    }

    async function onSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setMessage(null);

        if (!isAuthenticated) {
            setMessage("Будь ласка, увійдіть в акаунт, щоб додати відстеження");
            return;
        }

        if (selectedTriggers.length === 0) {
            setMessage("Оберіть хоча б один тригер сповіщення");
            return;
        }

        const session = localStorage.getItem("anyalert:session");
        if (!session) {
            setMessage("Сесія застаріла. Будь ласка, увійдіть знову.");
            return;
        }

        let token: string;
        try {
            const parsed = JSON.parse(session) as { token?: unknown };
            if (typeof parsed.token !== "string" || parsed.token.trim().length === 0) {
                setMessage("Сесія невалідна. Будь ласка, увійдіть знову.");
                localStorage.removeItem("anyalert:session");
                return;
            }
            token = parsed.token;
        } catch {
            setMessage("Помилка авторизації.");
            return;
        }

        setIsSubmitting(true);

        try {
            for (const triggerType of selectedTriggers) {
                const val = triggerValues[triggerType].trim();
                const selectedOption = triggerOptionsByType[triggerType];

                if (selectedOption.inputLabel && !val) {
                    setMessage(`Вкажіть значення для тригера: ${selectedOption.title}`);
                    setIsSubmitting(false);
                    return;
                }

                let numericValue: number | null = null;

                if (selectedOption.inputLabel && val) {
                    numericValue = parseFloat(val.replace(",", "."));
                    if (Number.isNaN(numericValue)) {
                        setMessage(`Некоректне числове значення для тригера: ${selectedOption.title}`);
                        setIsSubmitting(false);
                        return;
                    }
                }

                await createTracker({
                    url: productUrl,
                    network: platform.slug,
                    trigger_type: triggerType,
                    trigger_value: selectedOption.inputLabel ? numericValue : null
                }, token);
            }

            setMessage("Успішно! Ми почали відстежувати цей товар. Сповіщення прийдуть на вашу пошту.");
            setProductUrl("");
            setSelectedTriggers(triggerOptions[0] ? [triggerOptions[0].type] : []);
            setTriggerValues(defaultTriggerValues);
        } catch (error) {
            console.error("Failed to create tracker:", error);
            setMessage("Не вдалося зберегти відстеження. Перевірте посилання або спробуйте пізніше.");
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <form className="tracking-form" onSubmit={onSubmit}>
            <label htmlFor="productUrl">Посилання на товар {platform.name}</label>
            <input
                id="productUrl"
                type="url"
                placeholder="https://example.com/product"
                value={productUrl}
                onChange={(event) => setProductUrl(event.target.value)}
                required
            />

            <fieldset className="trigger-group">
                <legend>Тригери сповіщення (можна обрати кілька)</legend>
                <div className="trigger-options">
                    {triggerOptions.map((option) => {
                        const isChecked = selectedTriggers.includes(option.type);

                        return (
                            <div key={option.type} className="trigger-option-card">
                                <label className="trigger-check">
                                    <input
                                        type="checkbox"
                                        checked={isChecked}
                                        onChange={() => toggleTrigger(option.type)}
                                    />
                                    <span>{option.title}</span>
                                </label>

                                {isChecked && option.inputLabel ? (
                                    <>
                                        <label htmlFor={`trigger-${option.type}`}>
                                            {option.inputLabel}
                                            {option.unitLabel ? ` (${option.unitLabel})` : ""}
                                        </label>
                                        <input
                                            id={`trigger-${option.type}`}
                                            type="text"
                                            placeholder={option.placeholder}
                                            value={triggerValues[option.type]}
                                            onChange={(event) =>
                                                setTriggerValues((current) => ({
                                                    ...current,
                                                    [option.type]: event.target.value
                                                }))
                                            }
                                        />
                                    </>
                                ) : null}
                            </div>
                        );
                    })}
                </div>
            </fieldset>

            <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Збереження..." : "Зберегти відстеження"}
            </button>
            {message ? <p className="form-message">{message}</p> : null}
        </form>
    );
}
