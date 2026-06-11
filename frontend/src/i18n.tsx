import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { ApiError, type Locale } from "./api";

const ruDictionary = {
    appName: "Renovation Estimator",
    home: "Главная",
    languageLabel: "Язык",
    newEstimate: "Новая смета",
    recentEstimates: "Последние сметы",
    emptyHome: "Создайте первую смету, чтобы она появилась в этом списке.",
    objectStep: "Объект и фото",
    roomsStep: "Комнаты и работы",
    title: "Название",
    address: "Адрес",
    photos: "Фото объекта",
    photosHint: "JPEG, PNG или WebP, до 10 файлов по 10 МБ.",
    next: "Далее",
    saveRoom: "Сохранить комнату",
    calculate: "Рассчитать",
    estimate: "Смета",
    share: "Поделиться",
    print: "Печать",
    readOnly: "Просмотр только для чтения",
    dimensions: "Размеры",
    openings: "Окна и двери",
    works: "Работы",
    addWindow: "Добавить окно",
    addDoor: "Добавить дверь",
    length: "Длина",
    width: "Ширина",
    height: "Высота",
    count: "Кол-во",
    includeCeiling: "Считать потолок",
    layers: "Слои",
    unitPrice: "Цена / м²",
    totals: "Итоги",
    subtotal: "Подытог",
    total: "Итого",
    vat: "TVA / НДС",
    editPrices: "Сохранить цены",
    area: "Площадь",
    labor: "Работа",
    material: "Материал",
    consumption: "Расход",
    packages: "Упаковки",
    open: "Открыть",
    backToEstimate: "К смете",
    error: "Ошибка",
    loading: "Загрузка",
    noRooms: "Комнаты пока не добавлены.",
    shareCopied: "Ссылка скопирована",
    photoUploadUnavailable: "Фото проверяются перед созданием сметы.",
    photoValidationMaxCount: "Максимум 10 фото",
    photoValidationUnsupportedType: "неподдерживаемый тип файла",
    photoValidationMaxSize: "максимум 10 МБ",
    errorMessages: {
      not_found: "Запись не найдена",
      "validation.title.string_too_short": "Укажите название",
      validation: "Проверьте заполненные поля",
      invalid_work_code: "Неизвестный тип работы",
      invalid_photo_mime: "Неподдерживаемый тип фото",
      invalid_photo_magic: "Содержимое фото не совпадает с типом файла",
      photo_too_large: "Фото больше 10 МБ",
      too_many_photos: "В смете может быть не больше 10 фото",
      http_error: "Ошибка запроса",
      unknown: "Неизвестная ошибка"
    }
};

export type Dictionary = {
  [Key in keyof typeof ruDictionary]: Key extends "errorMessages"
    ? Record<keyof typeof ruDictionary.errorMessages, string>
    : string;
};

const dictionaries: Record<Locale, Dictionary> = {
  ru: ruDictionary,
  fr: {
    appName: "Renovation Estimator",
    home: "Accueil",
    languageLabel: "Langue",
    newEstimate: "Nouveau devis",
    recentEstimates: "Devis récents",
    emptyHome: "Créez un premier devis pour l’afficher ici.",
    objectStep: "Objet et photos",
    roomsStep: "Pièces et travaux",
    title: "Titre",
    address: "Adresse",
    photos: "Photos du chantier",
    photosHint: "JPEG, PNG ou WebP, jusqu’à 10 fichiers de 10 Mo.",
    next: "Suivant",
    saveRoom: "Enregistrer la pièce",
    calculate: "Calculer",
    estimate: "Devis",
    share: "Partager",
    print: "Imprimer",
    readOnly: "Lecture seule",
    dimensions: "Dimensions",
    openings: "Fenêtres et portes",
    works: "Travaux",
    addWindow: "Ajouter fenêtre",
    addDoor: "Ajouter porte",
    length: "Longueur",
    width: "Largeur",
    height: "Hauteur",
    count: "Qté",
    includeCeiling: "Inclure plafond",
    layers: "Couches",
    unitPrice: "Prix / m²",
    totals: "Totaux",
    subtotal: "Sous-total",
    total: "Total",
    vat: "TVA",
    editPrices: "Enregistrer prix",
    area: "Surface",
    labor: "Main d’œuvre",
    material: "Matériau",
    consumption: "Consommation",
    packages: "Lots",
    open: "Ouvrir",
    backToEstimate: "Voir le devis",
    error: "Erreur",
    loading: "Chargement",
    noRooms: "Aucune pièce ajoutée.",
    shareCopied: "Lien copié",
    photoUploadUnavailable: "Les photos sont vérifiées avant la création du devis.",
    photoValidationMaxCount: "Maximum 10 photos",
    photoValidationUnsupportedType: "type de fichier non pris en charge",
    photoValidationMaxSize: "maximum 10 Mo",
    errorMessages: {
      not_found: "Enregistrement introuvable",
      "validation.title.string_too_short": "Indiquez un titre",
      validation: "Vérifiez les champs saisis",
      invalid_work_code: "Type de travail inconnu",
      invalid_photo_mime: "Type de photo non pris en charge",
      invalid_photo_magic: "Le contenu de la photo ne correspond pas au type déclaré",
      photo_too_large: "La photo dépasse 10 Mo",
      too_many_photos: "Un devis ne peut pas contenir plus de 10 photos",
      http_error: "Erreur de requête",
      unknown: "Erreur inconnue"
    }
  }
};

const I18nContext = createContext<{
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: Dictionary;
} | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    const stored = localStorage.getItem("locale");
    return stored === "fr" ? "fr" : "ru";
  });
  const value = useMemo(
    () => ({
      locale,
      setLocale(nextLocale: Locale) {
        localStorage.setItem("locale", nextLocale);
        setLocaleState(nextLocale);
      },
      t: dictionaries[locale]
    }),
    [locale]
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used inside I18nProvider");
  }
  return context;
}

export function translateError(error: unknown, t: Dictionary): string {
  if (error instanceof ApiError) {
    if (error.code in t.errorMessages) {
      return t.errorMessages[error.code as keyof typeof t.errorMessages];
    }
    if (error.code.startsWith("validation.")) {
      return t.errorMessages.validation;
    }
    return t.errorMessages.unknown;
  }
  return error instanceof Error ? error.message : String(error);
}
