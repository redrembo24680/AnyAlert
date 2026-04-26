export interface MarketplacePlatform {
    slug: string;
    name: string;
    shortDescription: string;
    longDescription: string;
    accent: string;
    accentSoft: string;
    bannerFrom: string;
    bannerTo: string;
}

export const marketplacePlatforms: MarketplacePlatform[] = [
    {
        slug: "rozetka",
        name: "Rozetka",
        shortDescription: "Техніка, гаджети, дім та товари щоденного попиту.",
        longDescription:
            "Відстежуйте наявність і ціну популярних товарів із Rozetka без ручної перевірки сторінок.",
        accent: "#35a229",
        accentSoft: "#d8f3d4",
        bannerFrom: "#ebffe9",
        bannerTo: "#d8f3d4"
    },
    {
        slug: "olx",
        name: "OLX",
        shortDescription: "Оголошення від приватних продавців та малого бізнесу.",
        longDescription:
            "Слідкуйте за оновленнями товарів з OLX: зміна ціни, статусу або доступності оголошення.",
        accent: "#173a76",
        accentSoft: "#dbe8ff",
        bannerFrom: "#edf3ff",
        bannerTo: "#dbe8ff"
    },
    {
        slug: "prom",
        name: "Prom",
        shortDescription: "Маркетплейс товарів від багатьох українських продавців.",
        longDescription:
            "Автоматизуйте контроль цін та залишків у картках товарів на Prom для швидших рішень.",
        accent: "#7f3ff3",
        accentSoft: "#ede1ff",
        bannerFrom: "#f6f0ff",
        bannerTo: "#e6d6ff"
    },
    {
        slug: "allo",
        name: "ALLO",
        shortDescription: "Смартфони, електроніка та побутова техніка.",
        longDescription:
            "Налаштуйте тригери для товарів ALLO: зниження ціни, повернення у наявність та зміни знижки.",
        accent: "#f97316",
        accentSoft: "#ffe6d0",
        bannerFrom: "#fff1e6",
        bannerTo: "#ffe2cb"
    },
    {
        slug: "comfy",
        name: "Comfy",
        shortDescription: "Онлайн-каталог техніки та товарів для дому.",
        longDescription:
            "Отримуйте сигнал, коли на Comfy з'явилася вигідна ціна або змінилась доступність потрібної моделі.",
        accent: "#facc15",
        accentSoft: "#fff4b8",
        bannerFrom: "#fffbe5",
        bannerTo: "#fff2a8"
    },
    {
        slug: "foxtrot",
        name: "Foxtrot",
        shortDescription: "Ритейлер електроніки з широким асортиментом.",
        longDescription:
            "Нехай система сама відстежує товарні сторінки Foxtrot і повідомляє про важливі зміни.",
        accent: "#e11d48",
        accentSoft: "#ffd9e1",
        bannerFrom: "#ffeef2",
        bannerTo: "#ffdce5"
    }
];

export function findPlatformBySlug(slug: string): MarketplacePlatform | undefined {
    return marketplacePlatforms.find((platform) => platform.slug === slug);
}
