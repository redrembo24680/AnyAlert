"use client";

import { FormEvent, useState } from "react";

import type { MarketplacePlatform } from "@/features/tracking/data/platforms";

type TriggerType =
    | "price_drop"
    | "availability"
    | "discount"
    | "price_rise"
    | "seller_change"
    | "rating_drop";

interface TriggerOption {
    type: TriggerType;
    title: string;
    inputLabel: string;
    placeholder: string;
}

interface TrackingTrigger {
    type: TriggerType;
    value: string;
}

interface TrackingRecord {
    platform: string;
    productUrl: string;
    triggers: TrackingTrigger[];
    createdAt: string;
}

const TRACKING_KEY = "anyalert:tracking-records";

interface PlatformTrackingFormProps {
    platform: MarketplacePlatform;
}

const triggerOptions: TriggerOption[] = [
    {
        type: "price_drop",
        title: "Ціна опустилась нижче порогу",
        inputLabel: "Ціна нижче (грн)",
        placeholder: "Наприклад: 15999"
    },
    {
        type: "availability",
        title: "Змінилась наявність",
        inputLabel: "Стан (in_stock/out_of_stock)",
        placeholder: "Наприклад: in_stock"
    },
    {
        type: "discount",
        title: "Знижка стала більшою за поріг",
        inputLabel: "Знижка від (%)",
        placeholder: "Наприклад: 15"
    },
    {
        type: "price_rise",
        title: "Ціна виросла вище порогу",
        inputLabel: "Ціна вище (грн)",
        placeholder: "Наприклад: 22000"
    },
    {
        type: "seller_change",
        title: "Змінився продавець",
        inputLabel: "Очікуваний продавець",
        placeholder: "Наприклад: Rozetka"
    },
    {
        type: "rating_drop",
        title: "Рейтинг товару знизився",
        inputLabel: "Мінімальний рейтинг",
        placeholder: "Наприклад: 4.2"
    }
];

function readTrackingRecords(): TrackingRecord[] {
    if (typeof window === "undefined") {
        return [];
    }

    const raw = window.localStorage.getItem(TRACKING_KEY);
    if (!raw) {
        return [];
    }

    try {
        const parsed = JSON.parse(raw) as TrackingRecord[];
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
}

function writeTrackingRecords(records: TrackingRecord[]): void {
    if (typeof window === "undefined") {
        return;
    }

    window.localStorage.setItem(TRACKING_KEY, JSON.stringify(records));
}

export function PlatformTrackingForm({ platform }: PlatformTrackingFormProps) {
    const [productUrl, setProductUrl] = useState("");
    const [selectedTriggers, setSelectedTriggers] = useState<TriggerType[]>(["price_drop"]);
    const [triggerValues, setTriggerValues] = useState<Record<TriggerType, string>>({
        price_drop: "",
        availability: "",
        discount: "",
        price_rise: "",
        seller_change: "",
        rating_drop: ""
    });
    const [message, setMessage] = useState<string | null>(null);

    function toggleTrigger(triggerType: TriggerType) {
        setSelectedTriggers((current) => {
            if (current.includes(triggerType)) {
                return current.filter((item) => item !== triggerType);
            }

            return [...current, triggerType];
        });
    }

    function onSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setMessage(null);

        if (selectedTriggers.length === 0) {
            setMessage("Оберіть хоча б один тригер сповіщення");
            return;
        }

        const normalizedTriggers = selectedTriggers.map((triggerType) => ({
            type: triggerType,
            value: triggerValues[triggerType].trim()
        }));

        const hasEmptyValue = normalizedTriggers.some((trigger) => !trigger.value);
        if (hasEmptyValue) {
            setMessage("Для кожного обраного тригера заповніть значення");
            return;
        }

        const records = readTrackingRecords();
        records.push({
            platform: platform.slug,
            productUrl,
            triggers: normalizedTriggers,
            createdAt: new Date().toISOString()
        });

        writeTrackingRecords(records);

        setMessage(
            "Готово. Це mock-режим: заявку збережено локально. Після інтеграції бекенду будемо надсилати реальні сповіщення."
        );
        setProductUrl("");
        setSelectedTriggers(["price_drop"]);
        setTriggerValues({
            price_drop: "",
            availability: "",
            discount: "",
            price_rise: "",
            seller_change: "",
            rating_drop: ""
        });
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

                                {isChecked ? (
                                    <>
                                        <label htmlFor={`trigger-${option.type}`}>{option.inputLabel}</label>
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

            <button type="submit">Зберегти відстеження</button>
            {message ? <p className="form-message">{message}</p> : null}
        </form>
    );
}
