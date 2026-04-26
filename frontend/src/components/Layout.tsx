import { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "react-oidc-context";
import { useTheme } from "../theme/ThemeContext";
import { useI18n } from "../i18n/I18nContext";
import logoClaro from "../modo-claro-logo.png";
import logoOscuro from "../modo-oscuro-logo.png";

interface LayoutProps { children: ReactNode; back?: boolean; title?: string; }

function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5"/>
      <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
      <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>
  );
}

export function Layout({ children, back = false, title }: LayoutProps) {
  const { theme, toggle } = useTheme();
  const { lang, toggle: toggleLang, tr } = useI18n();
  const auth = useAuth();
  const navigate = useNavigate();

  const userName = auth.user?.profile.name ?? auth.user?.profile.email ?? "Usuario";

  return (
    <div className="hscreen overflow-x-hidden">
      {/* Franja Bifrost */}
      <div className="h-[3px] w-full" style={{
        background: "linear-gradient(90deg, #1d4ed8 0%, #4f46e5 25%, #7c3aed 50%, #c026d3 70%, #c9a84b 100%)"
      }} />

      {/* Header */}
      <header style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--bg-header)" }}
        className="sticky top-[3px] z-10 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center gap-2 sm:gap-4 px-3 sm:px-6 py-4 sm:py-7">

          {back && (
            <button onClick={() => navigate(-1)} className="transition-colors p-1 flex-shrink-0 hover:text-[#c9a84b]"
              style={{ color: "var(--header-text)" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6"/>
              </svg>
            </button>
          )}

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 sm:gap-3 select-none group flex-shrink-0">
            <img
              src={theme === "dark" ? logoOscuro : logoClaro}
              alt="HeimdALL logo"
              className="h-14 w-14 sm:h-20 sm:w-20 object-contain transition-all duration-300"
            />
            <div className="leading-none">
              <div className="text-xs sm:text-sm font-black tracking-[0.15em] sm:tracking-[0.2em] uppercase"
                style={{ color: "var(--header-text)" }}>
                Heimd<span style={{ color: "#c9a84b" }}>ALL</span>
              </div>
              <div className="hidden sm:block text-[9px] tracking-[0.15em] uppercase mt-0.5"
                style={{ color: "var(--header-text)", opacity: 0.5 }}>
                {tr.accessPortal}
              </div>
            </div>
          </Link>

          {/* Título de página */}
          {title && (
            <div className="hidden sm:flex items-center gap-2 min-w-0">
              <span style={{ color: "var(--header-text)", opacity: 0.4 }}>/</span>
              <span className="text-sm truncate" style={{ color: "var(--header-text)", opacity: 0.7 }}>{title}</span>
            </div>
          )}

          <div className="ml-auto flex items-center gap-1 sm:gap-3">
            {/* Toggle idioma */}
            <button onClick={toggleLang} title={lang === "es" ? "Switch to English" : "Cambiar a Español"}
              className="rounded-lg px-2 py-1.5 text-[10px] font-bold tracking-widest transition-colors hover:text-[#c9a84b]"
              style={{ color: "var(--header-text)" }}>
              {lang === "es" ? "EN" : "ES"}
            </button>

            {/* Toggle tema */}
            <button onClick={toggle} title={theme === "dark" ? tr.modeLight : tr.modeDark}
              className="rounded-lg p-2 transition-colors hover:text-[#c9a84b]"
              style={{ color: "var(--header-text)" }}>
              {theme === "dark" ? <SunIcon /> : <MoonIcon />}
            </button>

            {/* Separador + nombre */}
            <div className="hidden sm:flex items-center gap-3">
              <div className="h-4 w-px" style={{ backgroundColor: "var(--header-text)", opacity: 0.2 }} />
              <span className="text-sm truncate max-w-[140px]" style={{ color: "var(--header-text)", opacity: 0.6 }}>
                {userName}
              </span>
            </div>

            {/* Salir */}
            <button onClick={() => auth.signoutRedirect()}
              className="flex items-center gap-1.5 rounded-lg p-2 sm:px-3 transition-colors hover:text-red-500"
              style={{ color: "var(--header-text)" }}>
              <LogoutIcon />
              <span className="hidden sm:inline text-sm">{tr.logout}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Contenido principal */}
      <main className="mx-auto w-full max-w-5xl px-3 sm:px-6 py-6 sm:py-10">
        {children}
      </main>
    </div>
  );
}
