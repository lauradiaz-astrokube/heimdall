import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { Lang, t } from "./translations";

interface I18nCtx {
  lang: Lang;
  toggle: () => void;
  tr: typeof t["es"];
}

const I18nContext = createContext<I18nCtx>({
  lang: "es",
  toggle: () => {},
  tr: t.es,
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    const stored = localStorage.getItem("hlang");
    if (stored === "es" || stored === "en") return stored;
    return navigator.language.startsWith("en") ? "en" : "es";
  });

  useEffect(() => {
    localStorage.setItem("hlang", lang);
  }, [lang]);

  const toggle = () => setLang((l) => (l === "es" ? "en" : "es"));

  return (
    <I18nContext.Provider value={{ lang, toggle, tr: t[lang] }}>
      {children}
    </I18nContext.Provider>
  );
}

export const useI18n = () => useContext(I18nContext);
