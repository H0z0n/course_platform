import type { ThemePreference } from "../api/types";
import { MonitorIcon, MoonIcon, SunIcon } from "../components/Icons";
import { useTheme } from "./ThemeContext";

const OPTIONS: { value: ThemePreference; label: string; Icon: typeof SunIcon }[] = [
  { value: "light", label: "Светлая тема", Icon: SunIcon },
  { value: "dark", label: "Тёмная тема", Icon: MoonIcon },
  { value: "system", label: "Как в системе", Icon: MonitorIcon },
];

export function ThemeSwitcher() {
  const { preference, setPreference } = useTheme();
  return (
    <div className="theme-switcher" role="radiogroup" aria-label="Тема оформления">
      {OPTIONS.map(({ value, label, Icon }) => (
        <button
          key={value}
          type="button"
          role="radio"
          aria-checked={preference === value}
          aria-label={label}
          title={label}
          className={preference === value ? "is-active" : ""}
          onClick={() => setPreference(value)}
        >
          <Icon />
        </button>
      ))}
    </div>
  );
}
