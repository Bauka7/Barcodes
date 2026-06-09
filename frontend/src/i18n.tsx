import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type Language = "ru" | "kk";

const LANGUAGE_STORAGE_KEY = "qazpost.language";

const dictionary = {
  ru: {
    appName: "QazPost SHPI",
    login: "Войти",
    username: "Логин",
    password: "Пароль",
    logout: "Выйти",
    departments: "Departments",
    generate: "Generate Barcode",
    history: "History",
    search: "Search SHPI",
    pdf: "PDF / Print",
    printHistory: "Print History",
    refresh: "Обновить",
    loading: "Загрузка...",
    noData: "Нет данных",
    selectedDepartment: "Выбранное отделение",
    selectDepartmentFirst: "Сначала выберите отделение",
    openDepartments: "Открыть Departments",
  },
  kk: {
    appName: "QazPost SHPI",
    login: "Кіру",
    username: "Логин",
    password: "Құпиясөз",
    logout: "Шығу",
    departments: "Departments",
    generate: "Generate Barcode",
    history: "History",
    search: "Search SHPI",
    pdf: "PDF / Print",
    printHistory: "Print History",
    refresh: "Жаңарту",
    loading: "Жүктелуде...",
    noData: "Дерек жоқ",
    selectedDepartment: "Таңдалған бөлімше",
    selectDepartmentFirst: "Алдымен бөлімшені таңдаңыз",
    openDepartments: "Departments ашу",
  },
};

type TranslationKey = keyof typeof dictionary.ru;

interface I18nContextValue {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: TranslationKey) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function getInitialLanguage(): Language {
  const storedLanguage = localStorage.getItem(LANGUAGE_STORAGE_KEY);
  return storedLanguage === "kk" ? "kk" : "ru";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(getInitialLanguage);

  function setLanguage(nextLanguage: Language): void {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, nextLanguage);
    setLanguageState(nextLanguage);
  }

  const value = useMemo<I18nContextValue>(
    () => ({
      language,
      setLanguage,
      t: (key) => dictionary[language][key],
    }),
    [language],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext);

  if (!context) {
    throw new Error("useI18n must be used within I18nProvider");
  }

  return context;
}
